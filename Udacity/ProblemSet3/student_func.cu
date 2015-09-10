/* Udacity Homework 3
   HDR Tone-mapping

  Background HDR
  ==============

  A High Dynamic Range (HDR) image contains a wider variation of intensity
  and color than is allowed by the RGB format with 1 byte per channel that we
  have used in the previous assignment.  

  To store this extra information we use single precision floating point for
  each channel.  This allows for an extremely wide range of intensity values.

  In the image for this assignment, the inside of church with light coming in
  through stained glass windows, the raw input floating point values for the
  channels range from 0 to 275.  But the mean is .41 and 98% of the values are
  less than 3!  This means that certain areas (the windows) are extremely bright
  compared to everywhere else.  If we linearly map this [0-275] range into the
  [0-255] range that we have been using then most values will be mapped to zero!
  The only thing we will be able to see are the very brightest areas - the
  windows - everything else will appear pitch black.

  The problem is that although we have cameras capable of recording the wide
  range of intensity that exists in the real world our monitors are not capable
  of displaying them.  Our eyes are also quite capable of observing a much wider
  range of intensities than our image formats / monitors are capable of
  displaying.

  Tone-mapping is a process that transforms the intensities in the image so that
  the brightest values aren't nearly so far away from the mean.  That way when
  we transform the values into [0-255] we can actually see the entire image.
  There are many ways to perform this process and it is as much an art as a
  science - there is no single "right" answer.  In this homework we will
  implement one possible technique.

  Background Chrominance-Luminance
  ================================

  The RGB space that we have been using to represent images can be thought of as
  one possible set of axes spanning a three dimensional space of color.  We
  sometimes choose other axes to represent this space because they make certain
  operations more convenient.

  Another possible way of representing a color image is to separate the color
  information (chromaticity) from the brightness information.  There are
  multiple different methods for doing this - a common one during the analog
  television days was known as Chrominance-Luminance or YUV.

  We choose to represent the image in this way so that we can remap only the
  intensity channel and then recombine the new intensity values with the color
  information to form the final image.

  Old TV signals used to be transmitted in this way so that black & white
  televisions could display the luminance channel while color televisions would
  display all three of the channels.
  

  Tone-mapping
  ============

  In this assignment we are going to transform the luminance channel (actually
  the log of the luminance, but this is unimportant for the parts of the
  algorithm that you will be implementing) by compressing its range to [0, 1].
  To do this we need the cumulative distribution of the luminance values.

  Example
  -------

  input : [2 4 3 3 1 7 4 5 7 0 9 4 3 2]
  min / max / range: 0 / 9 / 9

  histo with 3 bins: [4 7 3]

  cdf : [4 11 14]


  Your task is to calculate this cumulative distribution by following these
  steps.

*/


#include "reference_calc.cpp"
#include "utils.h"
#include <limits.h>
#include <float.h>
#include <math.h>
#include <stdio.h>

int get_max_size(int n, int d) {
    int size = n/d;
    if (n%d !=0 )
    {
        size = size+1;
    }
    return size;
}

__global__ 
void scan_kernel(unsigned int* d_bins, int size) {
    int mid = threadIdx.x + blockDim.x * blockIdx.x;
    if(mid >= size)
        return;
    
    for(int s = 1; s <= size; s *= 2) {
          int spot = mid - s; 
         
          unsigned int val = 0;
          if(spot >= 0)
              val = d_bins[spot];
          __syncthreads();
          if(spot >= 0)
              d_bins[mid] += val;
          __syncthreads();

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

__global__ void localHistograms (const float *input,
                                 unsigned int *output,
                                 const int size,
                                 int numBins,
                                 float min_logLum,
                                 float range,
                                 int perThreadReads)
{
    extern __shared__ unsigned int sdata2[];
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    //int tid = threadIdx.x;
    //printf("myX is %d and myX*perThreadReads is %d and size is %d\n",myX,myX*perThreadReads,size);
    for (int i = 0 ; i < numBins; i++)
    {
        sdata2[i] = 0;
    }

    for (int i=0;i<perThreadReads;i++)
    {
        if (myX*perThreadReads+i < size)
        {
            double lum = input[myX*perThreadReads+i];
            int bin = (lum - min_logLum) / range * numBins;
            sdata2[bin] = sdata2[bin]+1;
        }
    }
    for (int i = 0 ; i < numBins; i++)
    {
        output[blockIdx.x*numBins+i] = sdata2[i];
    }
}
__global__ void minmaxLuminance(const float* input,
                             float* output,
                             const int size,
                             int minmax)
{
    //minmax = 0 - min
    //min max = 1 - max
    
    extern __shared__ float sdata[];
    
    int myX = blockDim.x*blockIdx.x + threadIdx.x;
    int tid = threadIdx.x;
    if (myX >= size)
    {
        if (minmax == 0)
        {
            sdata[tid] = FLT_MAX;
        }
        else
        {
            sdata[tid] = -FLT_MAX;
        }
    }
    else
    {
        sdata[tid] = input[myX];
    }
    __syncthreads();

    if (myX >= size)
    {
        if (tid == 0)
        {
            if (minmax == 0)
            {
                output[blockIdx.x] = FLT_MAX;
            }
            else
            {
                output[blockIdx.x] = -FLT_MAX;
            }
        }
        return;
    }

    for (unsigned int s = blockDim.x/2; s > 0; s/=2)
    {
        if (tid < s)
        {
            if (minmax == 0)
            {
                sdata[tid] = min(sdata[tid],sdata[tid + s]);
            }
            else
            {
                sdata[tid] = max(sdata[tid],sdata[tid + s]);
            }
        }
        __syncthreads();
    }
    //printf("BlockIdx.x - %d\n",blockIdx.x);
    if (tid == 0)
    {
        output[blockIdx.x] = sdata[0];
    }
}

void calculateBins(unsigned int *d_finalHist, 
              const float* const d_logLuminance,
              const size_t numBins,
              const size_t numRows,
              const size_t numCols,
              float min_logLum,
              float range)
{
    unsigned int *d_histBins;
    int numThreadsPerBlock = 512;
    int size = numRows*numCols;
    printf("Size is %d\n",size);
    dim3 blockDim(1);
    dim3 gridDim(numThreadsPerBlock);
    int sizeOfBins = numBins*sizeof(unsigned int)*numThreadsPerBlock;
    int perThreadReads = get_max_size(size,numThreadsPerBlock);
    checkCudaErrors(cudaMalloc(&d_histBins, sizeOfBins));
    localHistograms<<<gridDim,blockDim,numBins*sizeof(unsigned int)>>>(d_logLuminance,d_histBins,size,numBins,min_logLum,range,perThreadReads);
    cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());
    
    size = numThreadsPerBlock;
    int localHistThreadsPerBlock = 8;
    dim3 blockDimLocalHist(localHistThreadsPerBlock);
    
    unsigned int* d_curr_in;
    unsigned int* d_curr_out;
    checkCudaErrors(cudaMalloc(&d_curr_in, numBins*sizeof(unsigned int)*numThreadsPerBlock));    
    checkCudaErrors(cudaMemcpy(d_curr_in, d_histBins, numBins*sizeof(unsigned int)*numThreadsPerBlock, cudaMemcpyDeviceToDevice));
    
    //unsigned int h_temp[1024*512];
    //checkCudaErrors(cudaMemcpy(&h_temp, d_histBins,  numBins*sizeof(unsigned int)*numThreadsPerBlock, cudaMemcpyDeviceToHost));
    //for(int i = 1024*511; i < 1024*512; i++)
    //    printf("hist out %d\n", h_temp[i]);
    while (size != 1 )
    {
        dim3 gridDimLocalHist(get_max_size(size,localHistThreadsPerBlock));
        printf("Histogram Reduce - Block Size - %d with size - %d\n",gridDimLocalHist.x,size);
        //Allocate d_curr_out here
        checkCudaErrors(cudaMalloc(&d_curr_out, numBins*sizeof(unsigned int) * get_max_size(size,localHistThreadsPerBlock)));
        
        //Call Kernel
        histogramReduce<<<gridDimLocalHist,blockDimLocalHist,numBins*sizeof(unsigned int)*localHistThreadsPerBlock>>>(numBins,d_curr_in,d_curr_out,size);
        
        cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());
        
        checkCudaErrors(cudaFree(d_curr_in));
        d_curr_in = d_curr_out;
        
        //Update size here
        size = get_max_size(size,localHistThreadsPerBlock);
    }
    checkCudaErrors(cudaFree(d_histBins));
    checkCudaErrors(cudaMemcpy(d_finalHist, d_curr_out, sizeof(unsigned int)*numBins, cudaMemcpyDeviceToDevice));
    checkCudaErrors(cudaFree(d_curr_out));
}

float findRange (const float* const d_logLuminance, 
                 const size_t numRows,
                 const size_t numCols,
                 int minmax)
{
    float returnValue;
    //Write code here
    int size = numRows*numCols;
    
    int numThreadsInBlock = 32;
    dim3 threadDim(numThreadsInBlock);
    
    float *d_curr_out;
    float *d_curr_in;
    checkCudaErrors(cudaMalloc(&d_curr_in, sizeof(float) * size));    
    checkCudaErrors(cudaMemcpy(d_curr_in, d_logLuminance, sizeof(float) * size, cudaMemcpyDeviceToDevice));
    
    int shmem_size = numThreadsInBlock;//Number of threads in a block;
    while (size != 1 )
    {
        dim3 blockDim(get_max_size(size,numThreadsInBlock));
        printf("MinMax - Block Size - %d\n",blockDim.x);
        //Allocate d_curr_out here
        checkCudaErrors(cudaMalloc(&d_curr_out, sizeof(float) * get_max_size(size,numThreadsInBlock)));
        
        //Call Kernel
        minmaxLuminance<<<blockDim,threadDim,shmem_size>>>(d_curr_in,d_curr_out, size,minmax);
        
        cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());
        
        checkCudaErrors(cudaFree(d_curr_in));
        d_curr_in = d_curr_out;
        
        //Update size here
        size = get_max_size(size,numThreadsInBlock);
    }
    
    checkCudaErrors(cudaMemcpy(&returnValue, d_curr_out, sizeof(float), cudaMemcpyDeviceToHost));
    checkCudaErrors(cudaFree(d_curr_out));
    return returnValue;
}

void your_histogram_and_prefixsum(const float* const d_logLuminance,
                                  unsigned int* const d_cdf,
                                  float &min_logLum,
                                  float &max_logLum,
                                  const size_t numRows,
                                  const size_t numCols,
                                  const size_t numBins)
{
  //TODO
  /*Here are the steps you need to implement
    1) find the minimum and maximum value in the input logLuminance channel
       store in min_logLum and max_logLum
    2) subtract them to find the range
    3) generate a histogram of all the values in the logLuminance channel using
       the formula: bin = (lum[i] - lumMin) / lumRange * numBins
    4) Perform an exclusive scan (prefix sum) on the histogram to get
       the cumulative distribution of luminance values (this should go in the
       incoming d_cdf pointer which already has been allocated for you)       */
    
    // 1
    min_logLum = findRange(d_logLuminance,numRows,numCols,0);
    max_logLum = findRange(d_logLuminance,numRows,numCols,1);
    printf("got min of %f\n", min_logLum);
    printf("got max of %f\n", max_logLum);
    // 2
    float range = max_logLum - min_logLum;
    printf("got range of %f\n", range);
    // 3
    unsigned int *d_histBins;
    int sizeOfBins = sizeof(unsigned int)*numBins;
    checkCudaErrors(cudaMalloc(&d_histBins, sizeOfBins));
    calculateBins(d_histBins, d_logLuminance, numBins,numRows,numCols,min_logLum,range);
    unsigned int h_out[100];
    cudaMemcpy(&h_out, d_histBins, sizeof(unsigned int)*100, cudaMemcpyDeviceToHost);
    
    // 4
    
    dim3 thread_dim(1024);
    dim3 scan_block_dim(get_max_size(numBins, thread_dim.x));
    scan_kernel<<<scan_block_dim, thread_dim>>>(d_histBins, numBins);
    cudaDeviceSynchronize(); checkCudaErrors(cudaGetLastError());    
    cudaMemcpy(d_cdf, d_histBins, sizeOfBins, cudaMemcpyDeviceToDevice);
    checkCudaErrors(cudaFree(d_histBins));
}
