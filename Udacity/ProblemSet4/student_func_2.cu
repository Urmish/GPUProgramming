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

#define BLOCK_SIZE 512
int get_max_size (int a, int d)
{
    int temp = a/d;
    if (a%d != 0)
    {
        temp = temp+1;
    }
    return temp;
}

#define gpuErrchk(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true)
{
   if (code != cudaSuccess) 
   {
      fprintf(stderr,"GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
      if (abort) exit(code);
   }
}

__global__ void fixup(unsigned int *input, unsigned int *aux, int len) {
    unsigned int t = threadIdx.x, start = 2 * blockIdx.x * BLOCK_SIZE;
    if (blockIdx.x > 0) {
       if (start + t < len)
          input[start + t] += aux[blockIdx.x ];
       if (start + BLOCK_SIZE + t < len)
          input[start + BLOCK_SIZE + t] += aux[blockIdx.x ];
    }
}

__global__ void scanPart1 (unsigned int* input,
			   unsigned int* output,
			   unsigned int* aux,
			   int numElems)
{
	extern __shared__ unsigned int sdata[];
	//int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	int lastReadValue = 0;
	//Input Read
	if (start + myLocalId < numElems)
	{
       		sdata[myLocalId] = input[start + myLocalId];
	}
	else
	{
       		sdata[myLocalId] = 0;
	}
	if (start + BLOCK_SIZE + myLocalId  < numElems)
	{
       		sdata[BLOCK_SIZE + myLocalId] = input[start + BLOCK_SIZE + myLocalId];
	}
    	else
	{
       		sdata[BLOCK_SIZE + myLocalId] = 0;
	}
	__syncthreads();
	lastReadValue = sdata[2*BLOCK_SIZE-1];
	
	//Reduction
	int stride;
	for (stride = 1; stride <= BLOCK_SIZE; stride <<= 1) 
	{
       		int index = (myLocalId + 1) * stride * 2 - 1;
	        if (index < 2 * BLOCK_SIZE)
 	        	sdata[index] += sdata[index - stride];
	        __syncthreads();
	}
	if (myLocalId == 0)
	{
		sdata[2*BLOCK_SIZE-1] = 0;
	}
	__syncthreads();
	// Post reduction
	for (stride = BLOCK_SIZE ; stride; stride >>= 1) 
	{
       		int index = (myLocalId + 1) * stride * 2 - 1;
	        //if (index + stride < 2 * BLOCK_SIZE)
	        if (index < 2 * BLOCK_SIZE)
		{
//			unsigned int temp = sdata[index+stride];
//         		sdata[index + stride] += sdata[index];
//			sdata[index] = temp;
			unsigned int temp = sdata[index];
         		sdata[index] += sdata[index-stride];
			sdata[index-stride] = temp;
		}
	        __syncthreads();
    	}

	if (start + myLocalId < numElems)
	       	output[start + myLocalId] = sdata[myLocalId];
	if (start + BLOCK_SIZE + myLocalId < numElems)
        	output[start + BLOCK_SIZE + myLocalId] = sdata[BLOCK_SIZE + myLocalId];

	if (myLocalId == 0 && aux!=NULL)
       		aux[blockIdx.x] = sdata[2 * BLOCK_SIZE - 1] + lastReadValue;
}

__global__ void splitInput(int compareAndValue,
			   unsigned int* input,
			   unsigned int* output,
			   int maxElements)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	if (myGlobalId >= maxElements)
	{
		return;
	}
	if(((input[myGlobalId] & compareAndValue)) > 0)
	{
		//printf("%d. %d & %d is 0\n",myGlobalId,input[myGlobalId],compareAndValue);
		output[myGlobalId] = 0;
	}
	else
	{
		//printf("%d. %d & %d is 1\n",myGlobalId,input[myGlobalId],compareAndValue);
		output[myGlobalId] = 1;
	}
	//printf("%d. %d\n",myGlobalId,input[myGlobalId]);
}

__global__ void possibleLocations (unsigned int* input,
				   unsigned int* input_scan,
				   unsigned int* output,
				   unsigned int numElems,
				   unsigned int compareAndValue)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	int total = input_scan[numElems-1] + (((input[numElems-1] & compareAndValue) > 0)?0:1);
	//printf("Total %d\n",total);
	if (myLocalId + start < numElems)
	{
		//output[myGlobalId] = myGlobalId - input_scan[myGlobalId] + total;
		output[start + myLocalId] = start + myLocalId  - input_scan[start + myLocalId] + total;
		//printf("%d. %d might go to %d\n",start + myLocalId,input[myLocalId + start], output[start + myLocalId]);
	}
	if (myLocalId + start + BLOCK_SIZE < numElems)
	{
		output[start + myLocalId + BLOCK_SIZE] = start + myLocalId + BLOCK_SIZE - input_scan[start + myLocalId + BLOCK_SIZE] + total ;
		//printf("%d. %d might go to %d\n",start + myLocalId,input[myLocalId + start+BLOCK_SIZE], output[start + myLocalId + BLOCK_SIZE]);
	}
	
}


__global__ void finalLocations (   unsigned int* input,
				   unsigned int* input_scan,
				   unsigned int* input_vals,
				   unsigned int* d_setOneIfOne,
				   unsigned int* output,
				   unsigned int numElems,
                   unsigned int* inputPos,
                   unsigned int* outputPos)
{
	int myGlobalId = blockDim.x*blockIdx.x + threadIdx.x;
	int myLocalId = threadIdx.x;
	int start = 2 * blockIdx.x * BLOCK_SIZE; //Each block reads 2*BLOCK_SIZE so idx*this value is total inputs read
	if (myLocalId + start < numElems)
	{
		if (d_setOneIfOne[myLocalId + start] == 0)
		{
			output[input[myLocalId + start]] = input_vals[myLocalId + start];
            outputPos[input[myLocalId + start]] = inputPos[myLocalId + start];
			//printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start], input[myLocalId + start]);
		}	
		else
		{
			output[input_scan[myLocalId + start]] = input_vals[myLocalId + start];
            outputPos[input_scan[myLocalId + start]] = inputPos[myLocalId + start];
			//printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start], input_scan[myLocalId + start]);
		}
	}
	if (myLocalId + start + BLOCK_SIZE < numElems)
	{	
		if (d_setOneIfOne[myLocalId + start + BLOCK_SIZE] == 0)
		{
			output[input[myLocalId + start + BLOCK_SIZE]] = input_vals[myLocalId + start + BLOCK_SIZE];
            outputPos[input[myLocalId + start + BLOCK_SIZE]] = inputPos[myLocalId + start + BLOCK_SIZE];
			//printf("%d. %d goes to %d\n",myGlobalId, input_vals[myLocalId + start+ BLOCK_SIZE], input[myLocalId + start +BLOCK_SIZE]);
		}	
		else
		{
			output[input_scan[myLocalId + start + BLOCK_SIZE]] = input_vals[myLocalId + start + BLOCK_SIZE];
            outputPos[input_scan[myLocalId + start + BLOCK_SIZE]] = inputPos[myLocalId + start + BLOCK_SIZE];
			//printf("%d. %d goes to %d\n", myGlobalId, input_vals[myLocalId + start+BLOCK_SIZE] , input_scan[myLocalId + start +BLOCK_SIZE]);
		}
	}
}

void your_sort(unsigned int* const d_inputVals,
               unsigned int* const d_inputPos,
               unsigned int* const d_outputVals,
               unsigned int* const d_outputPos,
               const size_t numElems)
{
    unsigned int* d_setOneIfOne;
    unsigned int* d_possibleLocations;
    //unsigned int* d_finalLocations;
    unsigned int* d_scan;
    unsigned int* h_scan;
    //unsigned int* d_inputVals;
	h_scan = (unsigned int*)malloc(numElems*sizeof(unsigned int));
	gpuErrchk(cudaMalloc(&d_setOneIfOne, numElems*sizeof(unsigned int)));
    //gpuErrchk(cudaMalloc(&d_inputVals, numElems*sizeof(unsigned int)));
	gpuErrchk(cudaMalloc(&d_scan, numElems*sizeof(unsigned int)));
	gpuErrchk(cudaMalloc(&d_possibleLocations, numElems*sizeof(unsigned int)));
    unsigned int* h_setOneIfOne;
    //d_inputVals = d_inputVals_2;
	h_setOneIfOne = (unsigned int*)malloc(numElems*sizeof(unsigned int));
	for (int i=0;i<32;i++)
    {
		 //gpuErrchk(cudaMalloc(&d_finalLocations, numElems*sizeof(unsigned int)));
		 //printf("Round %d\n",i);
 	     gpuErrchk(cudaMemset(d_setOneIfOne,0, numElems*sizeof(unsigned int)));
 	     gpuErrchk(cudaMemset(d_scan,0, numElems*sizeof(unsigned int)));
	     int compareAndValue = 1 << i;
		 int numberThreadPerBlock = 512;
		 dim3 blockDim_si(numberThreadPerBlock);
		 dim3 gridDim_si(get_max_size(numElems,numberThreadPerBlock));
		 splitInput<<<gridDim_si,blockDim_si>>>(compareAndValue, d_inputVals, d_setOneIfOne, numElems);
	     //    gpuErrchk(cudaMemcpy(h_setOneIfOne, d_setOneIfOne, numElems*sizeof(unsigned int), cudaMemcpyDeviceToHost));
		 //for (int i=0;i<10;i++)
		 //{
		 //	printf("%d ", h_setOneIfOne[i]);
		 //	h_setOneIfOne[i] = 0;
		 //}
		 //printf("\n");
		 dim3 blockDim_sp(BLOCK_SIZE);
		 dim3 gridDim_sp(get_max_size(numElems,2*BLOCK_SIZE));
     	 unsigned int* d_aux;
     	 unsigned int* d_aux_scan;
		 unsigned int* h_aux;
	 	 gpuErrchk(cudaMalloc(&d_aux, get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int)));
	 	 gpuErrchk(cudaMalloc(&d_aux_scan, get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int)));
		 h_aux = (unsigned int*)malloc(get_max_size(numElems,2*BLOCK_SIZE)*sizeof(unsigned int));
		 //printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 scanPart1<<<gridDim_sp,blockDim_sp,BLOCK_SIZE*2*sizeof(unsigned int)>>> (d_setOneIfOne,d_scan,d_aux,numElems);	
	     //    gpuErrchk(cudaMemcpy(h_scan, d_scan, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));	
		 //for (int i=0;i<10;i++)
		 //{
		 //	printf("%d ", h_scan[i]);
		 //	h_scan[i] = 0;
		 //}
		 //printf("\n");
		 dim3 blockDim_sp2(get_max_size(numElems,2*BLOCK_SIZE));
	     //    gpuErrchk(cudaMemcpy(h_aux, d_aux, blockDim_sp2.x*sizeof(unsigned int), cudaMemcpyDeviceToHost));	
		 //for (int i=0;i<blockDim_sp2.x;i++)
		 //{
		 //	printf("%d ", h_aux[i]);
		 //	h_aux[i] = 0;
		 //}
		 //printf("\n");

		 //printf ("Size of Kernel is Grid - 1, Block - %d\n",blockDim_sp2.x);
		 scanPart1<<<1,blockDim_sp2,BLOCK_SIZE*2*sizeof(unsigned int)>>>(d_aux,d_aux_scan,NULL,blockDim_sp2.x);	
	     //gpuErrchk(cudaMemcpy(h_aux, d_aux_scan, blockDim_sp2.x*sizeof(unsigned int), cudaMemcpyDeviceToHost));	
		 //for (int i=0;i<blockDim_sp2.x;i++)
		 //{
		 //	printf("%d ", h_aux[i]);
		 //	h_aux[i] = 0;
		 //}
         
		 //printf("\n");
		 //printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 fixup<<<gridDim_sp,blockDim_sp>>>(d_scan,d_aux_scan,numElems);
	     gpuErrchk(cudaMemcpy(h_scan, d_scan, numElems*sizeof(unsigned int), cudaMemcpyDeviceToHost));	
		 //for (int i=0;i<10;i++)
		 //{
		 //	printf("%d ", h_scan[i]);
		 //	h_scan[i] = 0;
		 //}
		 //printf("h_scan - %d\n",h_scan[numElems-1]);
		 //printf ("Size of Kernel is Grid - %d, Block - %d\n",gridDim_sp.x,blockDim_sp.x);
		 possibleLocations<<<gridDim_sp,blockDim_sp>>>(d_inputVals,d_scan, d_possibleLocations, numElems, compareAndValue);
         //        gpuErrchk(cudaMemcpy(h_setOneIfOne, d_possibleLocations, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));
		 //printf ("Possible Locations are \n");
		 //for (int i=0;i<10;i++)
		 //{
		 //	printf("%d ", h_setOneIfOne[i]);
		 //	h_setOneIfOne[i] = 0;
		 //}
		 //printf ("\n");
		 //finalLocations<<<gridDim_sp,blockDim_sp>>>(d_possibleLocations,d_scan,d_inputVals, d_setOneIfOne, d_finalLocations,numElems,d_inputPos,d_outputPos);
         finalLocations<<<gridDim_sp,blockDim_sp>>>(d_possibleLocations,d_scan,d_inputVals, d_setOneIfOne, d_outputVals,numElems,d_inputPos,d_outputPos);
	 	 cudaDeviceSynchronize(); 
		 //gpuErrchk(cudaFree(d_inputVals));
		 //d_inputVals = d_finalLocations; 
         checkCudaErrors(cudaMemcpy(d_inputPos, d_outputPos, numElems*sizeof(unsigned int), cudaMemcpyDeviceToDevice));
         //checkCudaErrors(cudaMemcpy(d_inputVals, d_finalLocations, numElems*sizeof(unsigned int), cudaMemcpyDeviceToDevice));
         checkCudaErrors(cudaMemcpy(d_inputVals, d_outputVals, numElems*sizeof(unsigned int), cudaMemcpyDeviceToDevice));
         //gpuErrchk(cudaMemcpy(h_setOneIfOne, d_finalLocations, numElems*sizeof(numElems), cudaMemcpyDeviceToHost));
		 //printf ("\nFinal Positions are \n");
		 //for (int i=0;i<10;i++)
		 //{
		 //       printf("%d ", h_setOneIfOne[i]);
		 //       h_setOneIfOne[i] = 0;
		 //}

		 //printf("\n******************************************\n");
	         //printf("Histogram Values - %d %d %d %d %d \n", h_bins[0], h_bins[1], h_bins[0]+h_bins[1], numElems, compareAndValue);
    }
    //gpuErrchk(cudaMemcpy(d_outputVals, d_finalLocations, numElems*sizeof(numElems), cudaMemcpyDeviceToDevice));
    gpuErrchk(cudaFree(d_setOneIfOne));
    free(h_setOneIfOne);
    //gpuErrchk(cudaFree(d_possibleLocations));
    free(h_scan);
}
