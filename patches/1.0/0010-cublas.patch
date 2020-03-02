--- cmake/Cuda.cmake	2017-04-15 19:17:48.000000000 +0300
+++ cmake/Cuda.new.cmake	2020-03-02 18:30:27.000000000 +0300
@@ -233,6 +233,7 @@
 
 find_package(CUDA 5.5 QUIET)
 find_cuda_helper_libs(curand)  # cmake 2.8.7 compartibility which doesn't search for curand
+find_cuda_helper_libs(cublas)
 
 if(NOT CUDA_FOUND)
   return()
