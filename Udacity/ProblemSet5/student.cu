/* Udacity HW5
   Histogramming for Speed

   The goal of this assignment is compute a histogram
   as fast as possible.  We have simplified the problem as much as
   possible to allow you to focus solely on the histogramming algorithm.

   The input values that you need to histogram are already the exact
   bins that need to be updated.  This is unlike in HW3 where you needed
   to compute the range of the data and then do:
   bin = (val - valMin) / valRange to determine the bin.

   Here the bin is just:
   bin = val

   so the serial histogram calculation looks like:
   for (i = 0; i < numElems; ++i)
     histo[val[i]]++;

   That's it!  Your job is to make it run as fast as possible!

   The values are normally distributed - you may take
   advantage of this fact in your implementation.

*/


#include "utils.h"
#include "stdio.h"

int get_max_size(int n, int d) {
    int size = n/d;
    if (n%d !=0 )
    {
        size = size+1;
    }
    return size;
}

__global__ void localHistograms (const unsigned int* const input,
                                 unsigned int *output,
                                 const int size,
                                 int numBins,
                                 int perThreadReads)
{
    extern __shared__ unsigned int sdata2[];
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    //int tid = threadIdx.x;
    //printf("myX is %d and myX*perThreadReads is %d and size is %d\n",myX,myX*perThreadReads,size);
    sdata2[threadIdx.x] = 0;

    if(myX < size)
    {
        atomicAdd(&sdata2[input[myX]],1);
    }
    
    output[blockIdx.x*numBins+threadIdx.x] = sdata2[threadIdx.x];
    
}


__global__
void histoReduce(int numBins,
                 unsigned int *input,
                 unsigned int *output,
                 int size,
                 int numHistReducePerBlock)
{
    extern __shared__ unsigned int sdata3[];
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    int tid = threadIdx.x;
    for (int i=0;i<numHistReducePerBlock;i++)
    {
        int index = (blockIdx.x*numHistReducePerBlock+i)*numBins+threadIdx.x;
        if (blockIdx.x+i >= size)
        {
            sdata3[i*numBins + i] = 0;
        }
        else
        {
            sdata3[i*numBins + i] = input[index];
        }
    }
    __syncthreads();
    
    if (myX >= size)
    {
        output[blockIdx.x*numBins+threadIdx.x] = 0;
    }
    
    for (unsigned int s = numHistReducePerBlock/2; s > 0; s/=2)
    {
        for (int i=0;i<s;i++)
        {
            sdata3[i*numBins+tid] = sdata3[i*numBins+tid] + sdata3[i*numBins+s*numBins+tid];
        }
        __syncthreads();
    }
    
    output[blockIdx.x*numBins+threadIdx.x] = sdata3[threadIdx.x];
}

void computeHistogram(const unsigned int* const d_vals, //INPUT
                      unsigned int* const d_histo,      //OUTPUT
                      const unsigned int numBins,
                      const unsigned int numElems)
{
    unsigned int *d_histBins;
    int numThreadsPerBlock = 1024;
    printf("Size is %d\n",numElems);
    int perThreadReads = 1;
    dim3 blockDim(numThreadsPerBlock);
    dim3 gridDim(get_max_size(numElems,numThreadsPerBlock));
    int sizeOfBins = numBins*sizeof(unsigned int)*gridDim.x;
    printf("Grid Dimension %d\n",gridDim.x);
    checkCudaErrors(cudaMalloc(&d_histBins, sizeOfBins));
    printf("Numbins - %d\n",numBins);
    localHistograms<<<gridDim,blockDim,numBins*sizeof(unsigned int)>>>(d_vals,d_histBins,numElems,numBins,perThreadReads);
    cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());

    int size = gridDim.x;
    int localHistThreadsPerBlock = 1024;
    dim3 blockDimLocalHist(localHistThreadsPerBlock);
    
    unsigned int* d_curr_in;
    d_curr_in = d_histBins;
    unsigned int* d_curr_out;
    int numHistReducePerBlock = 8;
    while (size != 1 )
    {
        dim3 gridDimLocalHist(get_max_size(size,numHistReducePerBlock));
        int sharedMemorySize = numBins*sizeof(unsigned int)*numHistReducePerBlock;
        printf("Histogram Reduce - Block Size - %d with size - %d and shmem - %d\n",gridDimLocalHist.x,size,sharedMemorySize);
        //Allocate d_curr_out here
        checkCudaErrors(cudaMalloc(&d_curr_out, numBins*sizeof(unsigned int) * gridDimLocalHist.x));
        
        //Call Kernel
        histoReduce<<<gridDimLocalHist,blockDimLocalHist,sharedMemorySize>>>(numBins,d_curr_in,d_curr_out,size,numHistReducePerBlock);    
        cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());
        
        checkCudaErrors(cudaFree(d_curr_in));
        d_curr_in = d_curr_out;
        
        //Update size here
        size = get_max_size(size,numHistReducePerBlock);
    }
    //checkCudaErrors(cudaFree(d_histBins));
    checkCudaErrors(cudaMemcpy(d_histo, d_curr_out, sizeof(unsigned int)*numBins, cudaMemcpyDeviceToDevice));
    checkCudaErrors(cudaFree(d_curr_out));
}
