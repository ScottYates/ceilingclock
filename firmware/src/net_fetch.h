// Downloads a URL (following redirects) for the podcast feed lookup. Gives the Content-Type,
// then the body in chunks to sink until sink returns false or the body ends. Returns false if
// the request failed. On the clock: net_fetch_esp.cpp. In the simulator: sim/sim_hw.cpp.
#pragma once
#include <functional>
#include <string>
#include <cstddef>

bool netFetch(const char* url, std::string& contentType, const std::function<bool(const char*, size_t)>& sink);
