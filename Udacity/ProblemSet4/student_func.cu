//Udacity HW 4
//Radix Sorting

#include "reference_calc.cpp"
#include "utils.h"

/* Red Eye Removal
   ===============
   
   For this assignment we are implementing red eye removal.  This is
   accomplished by first creating a score for every pixel that tells us how
   likely it is to be a red eye pixel.  We have already done this for you - you
   are receiving the scores and need to sort them in ascending order so that we
   know which pixels to alter to remove the red eye.

   Note: ascending order == smallest to largest

   Each score is associated with a position, when you sort the scores, you must
   also move the positions accordingly.

   Implementing Parallel Radix Sort with CUDA
   ==========================================

   The basic idea is to construct a histogram on each pass of how many of each
   "digit" there are.   Then we scan this histogram so that we know where to put
   the output of each digit.  For example, the first 1 must come after all the
   0s so we have to know how many 0s there are to be able to start moving 1s
   into the correct position.

   1) Histogram of the number of occurrences of each digit
   2) Exclusive Prefix Sum of Histogram
   3) Determine relative offset of each digit
        For example [0 0 1 1 0 0 1]
                ->  [0 1 0 1 2 3 2]
   4) Combine the results of steps 2 & 3 to determine the final
      output location for each element and move it there

   LSB Radix sort is an out-of-place sort and you will need to ping-pong values
   between the input and output buffers we have provided.  Make sure the final
   sorted results end up in the output buffer!  Hint: You may need to do a copy
   at the end.

 */
#include <stdio.h>
int get_max_size (int a, int d)
{
    int temp = a/d;
    if (a%d != 0)
    {
        temp = temp+1;
    }
    return temp;
}
__global__ void createHistogramSlow ( unsigned int* d_bins,
                            unsigned int* const d_inputVals,
                            const size_t numElems,
                            int compareAndValue)
{
    int myId = blockDim.x*blockIdx.x + threadIdx.x;
    //int tid = threadIdx.x;
    if (myId < numElems)
    {
        if ((d_inputVals[myId] & compareAndValue) != 0)
        {
            atomicAdd(&d_bins[1], 1);
        }
        else
        {
            atomicAdd(&d_bins[0], 1);
        }
    }
}

__global__ void localHistograms (const unsigned int *input,
                                 unsigned int *output,
                                 const int size,
                                 int numBins,
                                 int perThreadReads,
                                 unsigned int compareAndValue,
                                 unsigned int *d_setOneIfOne)
{
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    for (int i=0;i<perThreadReads;i++)
    {
        if (myX*perThreadReads+i < size)
        {
            if ((input[myX*perThreadReads + i] & compareAndValue) != 0)
            {
                //Write to global Value
                output[myX*numBins + 1] = output[myX*numBins + 1]+1;
                d_setOneIfOne[myX] = 1;
            }
            else
            {
                //Write to global Value
                output[myX*numBins] = output[myX*numBins]+1;
                d_setOneIfOne[myX] = 0;
            }
        }
    }
}

__global__ void histogramReduce (int numBins,
                                 unsigned int *input,
                                 unsigned int *output,
                                 int size
                                )
{
    extern __shared__ unsigned int sdata3[];
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    int tid = threadIdx.x;
    for (int i=0;i<numBins;i++)
    {
        int index = myX*numBins+i;
        if (myX >= size)
        {
            sdata3[tid*numBins+i] = 0;
        }
        else
        {
            sdata3[tid*numBins+i] = input[index];
        }
    }
    __syncthreads();
    
    if (myX >= size)
    {
        if (tid == 0)
        {
            for (int i=0;i < numBins;i++)
            {
                output[blockIdx.x*numBins+i] = 0;
            }
        }
        return;
    }
    
    for (unsigned int s = blockDim.x/2; s > 0; s/=2)
    {
        if(tid < s)
        {
            for (int i=0;i<numBins;i++)
            {
                sdata3[tid*numBins+i] = sdata3[tid*numBins+i] + sdata3[tid*numBins+i+s*numBins];
            }
        }
        __syncthreads();
    }
    if (tid==0)
    {
        for (int i=0;i<numBins;i++)
        {
            //printf("Writing %d for bin value %d\n",sdata3[i],i);
            output[blockIdx.x*numBins+i] = sdata3[i];
        }
    }
}

void fastHistogram(unsigned int *d_finalHist, 
              unsigned int* const d_inputVals,
              const size_t numElems,
              unsigned int compareAndValue,
              unsigned int* d_setOneIfOne)
{
    int numBins = 2;
    unsigned int *d_histBins;
    int numBlocksPerGrid = 1024;
    int size = numElems;
    dim3 blockDim(1);
    dim3 gridDim(numBlocksPerGrid);
    int sizeOfBins = numBins*sizeof(unsigned int)*numBlocksPerGrid;
    int perThreadReads = get_max_size(size,numBlocksPerGrid);
    //Initialize temperory array variable
    checkCudaErrors(cudaMalloc(&d_histBins, sizeOfBins));
    checkCudaErrors(cudaMemset(d_histBins, 0, sizeOfBins));
    
    //Call first kernel
    localHistograms<<<gridDim,blockDim>>>(d_inputVals,d_histBins,size,numBins,perThreadReads,compareAndValue,d_setOneIfOne);
    cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());
    
    size = numBlocksPerGrid;
    int localHistThreadsPerBlock = numBlocksPerGrid;
    dim3 blockDimLocalHist(localHistThreadsPerBlock);   
    unsigned int* d_curr_in;
    d_curr_in = d_histBins; 

    dim3 gridDimLocalHist(get_max_size(size,localHistThreadsPerBlock));
    histogramReduce<<<gridDimLocalHist,blockDimLocalHist,numBins*sizeof(unsigned int)*localHistThreadsPerBlock>>>(numBins,d_curr_in,d_finalHist,size);        
    cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());      
    checkCudaErrors(cudaFree(d_curr_in));
}


void your_sort(unsigned int* const d_inputVals,
               unsigned int* const d_inputPos,
               unsigned int* const d_outputVals,
               unsigned int* const d_outputPos,
               const size_t numElems)
{
     unsigned int* d_bins;
     unsigned int  h_bins[2];
     const size_t histo_size = 2*sizeof(unsigned int);
     checkCudaErrors(cudaMalloc(&d_bins, histo_size));
     unsigned int* d_setOneIfOne;
     checkCudaErrors(cudaMalloc(&d_setOneIfOne, numElems*sizeof(numElems)));
     for (int i=0;i<32;i++)
     {
         checkCudaErrors(cudaMemset(d_bins, 0, histo_size));
         int compareAndValue = 1 << i;
         fastHistogram(d_bins,d_inputVals,numElems,compareAndValue,d_setOneIfOne);
         checkCudaErrors(cudaMemcpy(&h_bins, d_bins, histo_size, cudaMemcpyDeviceToHost));
         printf("Histogram Values - %d %d %d %d %d \n", h_bins[0], h_bins[1], h_bins[0]+h_bins[1], numElems, compareAndValue);
     }
     checkCudaErrors(cudaFree(d_bins));
}

