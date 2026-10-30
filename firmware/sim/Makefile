# PC simulator for the Ceiling Clock firmware.
# Compiles the real firmware sources (../src) against stand-ins for the ESP32 hardware in shim/.
# Needs ArduinoJson: run `pio pkg install` (or one `pio run`) in ../ first so .pio/libdeps exists.
FW  := ../src
AJ  := ../.pio/libdeps/esp32s3/ArduinoJson/src
CXX ?= g++
CXXFLAGS := -std=gnu++17 -O1 -g -Wall -Wno-unused-variable -Wno-unused-function -pthread \
            -Ishim -I$(FW) -I$(AJ) -DARDUINO=10819 -DARDUINOJSON_ENABLE_PROGMEM=0
OUT := build

all: $(OUT)/ceilingclock-sim

$(OUT)/main.o: $(FW)/main.cpp $(FW)/*.h shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -Dtime=sim_time -c $< -o $@
$(OUT)/settings.o: $(FW)/settings.cpp $(FW)/settings.h shim/*.h | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_hw.o: sim_hw.cpp shim/*.h shim/glcdfont.c | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/sim_main.o: sim_main.cpp | $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@
$(OUT)/ceilingclock-sim: $(OUT)/main.o $(OUT)/settings.o $(OUT)/sim_hw.o $(OUT)/sim_main.o
	$(CXX) $(CXXFLAGS) $^ -o $@
$(OUT):
	mkdir -p $(OUT)

# ---- browser build (WebAssembly) with the system clang + Ubuntu's wasm32 libraries:
#      apt install wasi-libc libc++-18-dev-wasm32 libc++abi-18-dev-wasm32 libclang-rt-18-dev-wasm32
WASM_CXX   ?= clang++
WASM_FLAGS := --target=wasm32-wasi --sysroot=/usr -std=gnu++17 -Oz -fno-exceptions \
              -DSIM_WASM -DSIM_NO_THREADS -DARDUINO=10819 -DARDUINOJSON_ENABLE_PROGMEM=0 \
              -Ishim -I$(FW) -I$(AJ) -Wno-unused-function
WASM_OUT   := ../../docs/demo/ceilingclock.wasm

wasm: $(WASM_OUT)
$(WASM_OUT): $(FW)/main.cpp $(FW)/settings.cpp $(FW)/*.h sim_hw.cpp sim_wasm.cpp shim/*.h
	mkdir -p $(OUT)/wasm $(dir $(WASM_OUT))
	$(WASM_CXX) $(WASM_FLAGS) -Dtime=sim_time -Dlocaltime_r=sim_localtime_r -Dmktime=sim_mktime -c $(FW)/main.cpp -o $(OUT)/wasm/main.o
	$(WASM_CXX) $(WASM_FLAGS) -c $(FW)/settings.cpp -o $(OUT)/wasm/settings.o
	$(WASM_CXX) $(WASM_FLAGS) -c sim_hw.cpp -o $(OUT)/wasm/sim_hw.o
	$(WASM_CXX) $(WASM_FLAGS) -c sim_wasm.cpp -o $(OUT)/wasm/sim_wasm.o
	$(WASM_CXX) $(WASM_FLAGS) -mexec-model=reactor $(OUT)/wasm/*.o -lc++abi -Wl,--strip-all -o $@
	python3 make_demo_page.py

run: all
	./$(OUT)/ceilingclock-sim

clean:
	rm -rf $(OUT)
.PHONY: all run clean wasm
