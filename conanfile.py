from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class CaffeConan(ConanFile):
    name = "caffe"
    description = "Caffe: a fast open framework for deep learning"
    topics = ("conan", "caffe", "deep-learning", "machine-learning")
    url = "https://github.com/bincrafters/conan-caffe"
    homepage = "http://caffe.berkeleyvision.org"
    license = "BSD-2"
    # Remove following lines if the target lib does not use CMake
    exports_sources = ["CMakeLists.txt", "patches/*"]
    generators = "cmake", "cmake_find_package"

    settings = "os", "arch", "compiler", "build_type"

    options = {"shared": [True, False],
               "fPIC": [True, False],
               "with_gpu": [True, False],
               "with_cudnn": [True, False],
               "with_opencv": [True, False],
               "with_leveldb": [True, False],
               "with_lmdb": [True, False]
               }
    default_options = {"shared": False,
                       "fPIC": True,
                       "with_gpu": False,
                       "with_cudnn": False,
                       "with_opencv": False,
                       "with_leveldb": False,
                       "with_lmdb": False
                       }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"


    def configure(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("This library is not compatible with Windows")

    def requirements(self):
        self.requires.add("boost/1.72.0")
        self.requires.add("glog/0.4.0")
        self.requires.add("gflags/2.2.2")
        self.requires.add("hdf5/1.10.6")
        # caffe supports those BLAS implementations: openblas, mkl, accelerate, atlas
        # Choose Accelerate for MAC and openblas otherwise
        if self.settings.os != "Macos":
            self.requires.add("openblas/0.3.7")
        if not tools.which("protoc"):
            self.requires("protobuf/3.9.1@bincrafters/stable")

    def build_requirements(self):
        # waiting for an official protoc binary
        if not tools.which("protoc"):
            self.build_requires("protoc_installer/3.9.1@bincrafters/stable")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_python"] = False
        cmake.definitions["BUILD_python_layer"] = False
        cmake.definitions["BUILD_docs"] = False

        cmake.definitions["CPU_ONLY"] = not self.options.with_gpu
        cmake.definitions["USE_OPENCV"] = self.options.with_opencv
        cmake.definitions["USE_LEVELDB"] = self.options.with_leveldb
        cmake.definitions["USE_LMDB"] = self.options.with_lmdb
        cmake.definitions["USE_CUDNN"] = self.options.with_cudnn

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def _prepare(self):
        # ensure that bundled cmake files are not used
        for module in ['Glog', 'GFlags']:
            os.unlink(os.path.join(self._source_subfolder, 'cmake', 'Modules', 'Find'+module+'.cmake'))
        # drop autogenerated CMake files for protobuf because they prevent 
        # `cmake/ProtoBuf.cmake` to detect Protobuf using system FindProtobuf
        for module in ['protobuf', 'protoc_installer']:
            if os.path.exists('Find'+module+'.cmake'):
                os.unlink('Find'+module+'.cmake')
        # do not build examples
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "add_subdirectory(examples)", "")
        # patch sources
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def build(self):
        self._prepare()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        # remove python bindings
        tools.rmdir(os.path.join(self.package_folder, 'python'))
        # remove cmake
        tools.rmdir(os.path.join(self.package_folder, 'share'))

    def package_info(self):
        self.cpp_info.libs = ["caffe", "proto"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m"]

        # pass options from Caffe_DEFINITIONS
        if not self.options.with_gpu:
            self.cpp_info.defines.append("CPU_ONLY")
        if self.options.with_opencv:
            self.cpp_info.defines.append("USE_OPENCV")
        if self.options.with_leveldb:
            self.cpp_info.defines.append("USE_LEVELDB")
        if self.options.with_lmdb:
            self.cpp_info.defines.append("USE_LMDB")
        if self.options.with_cudnn:
            self.cpp_info.defines.append("USE_CUDNN")
        if self.settings.os == "Macos":
            # not for all cases but usually works
            self.cpp_info.defines.append("USE_ACCELERATE")

        # fix export names
        self.cpp_info.names["cmake_find_package"] = "Caffe"
        self.cpp_info.names["cmake_find_package_multi"] = "Caffe"

