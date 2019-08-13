git clone https://github.com/MITSustainableDesignLab/Daysim.git
mkdir build
pushd build

# first, build RADIANCE
cmake -DBUILD_HEADLESS=on - DCMAKE_ISTALL_PREFIX=$HOME/Daysim ../Daysim
make
make install

# (modify CMakeLists.txt in place according to https://github.com/MITSustainableDesignLab/Daysim#mac)
awk '1;/^project/{print "add_definitions(-DDAYSIM)"}' Daysim/CMakeLists.txt > Daysim/CMakeLists.txt

# next, build the DAYSIM binaries
cmake -DBUILD_HEADLESS=on - DCMAKE_ISTALL_PREFIX=$HOME/Daysim ../Daysim
make
mv ./bin/rtrace ./bin/rtrace_dc && cp ./bin/* /usr/local/bin
