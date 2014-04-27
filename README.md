EasyYCM
=======

[YouCompleteMe] is very cool for writing C/C++ code in VIM, but yet a little
complex to configure the flags (especially including paths) for clang. EasyYCM
makes it easier!

EasyYCM is just a `.ycm_extra_conf.py`, which figures out the right flags by
`.project-deps` in your project directory. `.project-deps` is a bash source by
which you defines flags to compile source code in your project and which other
projects it depends on in an intuitive way.


Install
-------

1. Copy `.ycm_extra_conf.py`, or make a symbolic link, to your home directory.
2. (optional) Copy `shlib-easyycm`, or make a symbolic link, to somewhere in
   your search path for commands.


How To Use
----------

For example, you have a library named `libbed`, with the following directory
structure:

```
libbed
+-- src
|   +-- bed-internal.h
|   +-- bed.c
|   +-- wood
|   |   +-- wood.h
|   |   +-- wood.cxx
|   +-- ...
+-- include
+-- bed.h
```

Providing `bed.h` is the public interface of the library, other header files are
internal. `bed-internal.h` is included by `#include "bed-internal.h"` and
`wood.h` is included by `#include "wood/wood.h"`. Your can add a `.project-deps`
under `libbed/`, which looks like this:

```sh
. shlib-easyycm
CXXINCLUDES=$LOCALPATH/include
LOCAL_CXXINCLUDES=$LOCALPATH/src
```

`shlib-easyycm` is a bash library for EasyYCM, which defines the environment
variable `LOCALPATH` by the absolute path of `.project-deps`'s directory. YCM
works for your `libbed`!

Now you have created another project, `sleeping`, which depends on `libbed`:

```
.
+-- libbed
|   +-- ...
+-- sleeping
+-- src
|   +-- ...
+-- ...
```

Source code in `sleeping` includes `bed.h` by `#include "bed.h"`. Your C
preprocessor can find it as `-I../libbed/include` is defined in your Makefile,
but [YouCompleteMe] does not know of that. You can add a
`sleeping/.project-deps` like this:

```sh
. shlib-easyycm
import ../libbed
LOCAL_CXXINCLUDES=$LOCALPATH/src
```

`import` is a function provided by `shlib-easyycm`. Now, in your `sleeping`
project, [YouCompleteMe] will no longer complain about `bed.h` not found.


All Flags
---------

You can define the following flags in your `.project-deps`:

- `{LOCAL_,}{C,CXX}INCLUDES`: Path to find your header files. Different paths
  should be separated by colon (`:`).
- `{LOCAL_,}{C,CXX}SYSINCLUDES`: Header files search path for `-isystem`.
- `{LOCAL_,}{C,CXX}FLAGS`: Extra flags passing to C/C++ compiler.
- `{C,CXX}`: Compiler to compile your source code. Default to `gcc`/`g++`. It is
  used to figure out compiler-specific system including path. For example, for
  some Android NDK project you need to use the cross compiler provided by
  android-ndk, which searches for extra ndk-specific paths.

The flags with a `LOCAL_` prefix will invisible from dependent projects.


[YouCompleteMe]:https://github.com/Valloric/YouCompleteMe
