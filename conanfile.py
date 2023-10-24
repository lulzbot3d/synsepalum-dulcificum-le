import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, mkdir, AutoPackager
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version
from jinja2 import Template


required_conan_version = ">=1.58.0 <2.0.0"


class DulcificumConan(ConanFile):
    name = "dulcificum"
    description = "Dulcificum changes the flavor, or dialect, of 3d printer commands"
    author = "UltiMaker"
    license = ""
    url = "https://github.com/Ultimaker/synsepalum-dulcificum"
    homepage = "https://ultimaker.com"
    topics = ("cura", "curaengine", "gcode-generation", "3D-printing", "miraclegrue", "toolpath")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_extensive_warnings": [True, False],
        "with_apps": [True, False],
        "with_python_bindings": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_extensive_warnings": False,
        "with_apps": True,
        "with_python_bindings": True,
    }

    def set_version(self):
        if not self.version:
            self.version = "0.1.0-alpha"

    @property
    def _min_cppstd(self):
        return 20

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "11",
            "clang": "14",
            "apple-clang": "13",
            "msvc": "192",
            "visual_studio": "17",
        }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        copy(self, "*", os.path.join(self.recipe_folder, "src"), os.path.join(self.export_sources_folder, "src"))
        copy(self, "*", os.path.join(self.recipe_folder, "include"), os.path.join(self.export_sources_folder, "include"))
        copy(self, "*", os.path.join(self.recipe_folder, "test"), os.path.join(self.export_sources_folder, "test"))
        copy(self, "*", os.path.join(self.recipe_folder, "apps"), os.path.join(self.export_sources_folder, "apps"))
        copy(self, "*", os.path.join(self.recipe_folder, "pyDulcificum"), os.path.join(self.export_sources_folder, "pyDulcificum"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)
        self.cpp.package.libs = ["dulcificum"]

    def requirements(self):
        self.requires("nlohmann_json/3.11.2", transitive_headers = True)
        self.requires("range-v3/0.12.0")
        self.requires("spdlog/1.10.0")
        self.requires("ctre/3.7.2")
        self.requires("range-v3/0.12.0")
        if self.options.with_apps:
            self.requires("docopt.cpp/0.6.3")
        if self.options.with_python_bindings:
            self.requires("cpython/3.10.4")
            self.requires("pybind11/2.10.4")

    def build_requirements(self):
        self.test_requires("standardprojectsettings/[>=0.1.0]@ultimaker/stable")
        if not self.conf.get("tools.build:skip_test", False, check_type = bool):
            self.test_requires("gtest/[>=1.12.1]")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        check_min_vs(self, 191)
        if not is_msvc(self):
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )
        if is_msvc(self) and self.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} can not be built as shared on Visual Studio and msvc.")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_TESTS"] = not self.conf.get("tools.build:skip_test", False, check_type = bool)
        tc.variables["EXTENSIVE_WARNINGS"] = self.options.enable_extensive_warnings
        tc.variables["DULCIFICUM_VERSION"] = self.version

        tc.variables["WITH_APPS"] = self.options.with_apps
        if self.options.with_apps:
            tc.variables["APP_VERSION"] = self.version

        tc.variables["WITH_PYTHON_BINDINGS"] = self.options.with_python_bindings
        if self.options.with_python_bindings:
            tc.variables["Python_EXECUTABLE"] = self.deps_user_info["cpython"].python.replace("\\", "/")
            tc.variables["Python_USE_STATIC_LIBS"] = not self.options["cpython"].shared
            tc.variables["Python_ROOT_DIR"] = self.deps_cpp_info["cpython"].rootpath.replace("\\", "/")
            tc.variables["Python_FIND_FRAMEWORK"] = "NEVER"
            tc.variables["Python_FIND_REGISTRY"] = "NEVER"
            tc.variables["Python_FIND_IMPLEMENTATIONS"] = "CPython"
            tc.variables["Python_FIND_STRATEGY"] = "LOCATION"
            tc.variables["PYDULCIFICUM_VERSION"] = self.version

        if is_msvc(self):
            tc.variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

        tc = VirtualBuildEnv(self)
        tc.generate(scope = "build")

        for dep in self.dependencies.values():
            if len(dep.cpp_info.libdirs) > 0:
                copy(self, "*.dylib", dep.cpp_info.libdirs[0], self.build_folder)
                copy(self, "*.dll", dep.cpp_info.libdirs[0], self.build_folder)
            if len(dep.cpp_info.bindirs) > 0:
                copy(self, "*.dll", dep.cpp_info.bindirs[0], self.build_folder)
            if not self.conf.get("tools.build:skip_test", False, check_type = bool):
                test_path = os.path.join(self.build_folder,  "tests")
                if not os.path.exists(test_path):
                    mkdir(self, test_path)
                if len(dep.cpp_info.libdirs) > 0:
                    copy(self, "*.dylib", dep.cpp_info.libdirs[0], os.path.join(self.build_folder,  "tests"))
                    copy(self, "*.dll", dep.cpp_info.libdirs[0], os.path.join(self.build_folder,  "tests"))
                if len(dep.cpp_info.bindirs) > 0:
                    copy(self, "*.dll", dep.cpp_info.bindirs[0], os.path.join(self.build_folder,  "tests"))

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        packager = AutoPackager(self)
        packager.run()
