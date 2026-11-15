// Downloads a URL (following redirects) for the podcast feed lookup. Gives the Content-Type,
// then the body in chunks to sink until sink returns false or the body ends. Returns false if
// the request failed. In net_fetch_esp.cpp (the simulator supplies its own HTTPClient underneath).
#pragma once
#include <functional>
#include <string>
#include <cstddef>

bool netFetch(const char* url, std::string& contentType, const std::function<bool(const char*, size_t)>& sink);
