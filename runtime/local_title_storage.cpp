#include "local_title_storage.h"
#include <algorithm>
#include <cctype>
#include <stdexcept>
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

namespace happywars {
namespace {
constexpr uint64_t kQuota=64*1024*1024;
constexpr std::string_view kGroup="/storage/titlestorage/titlegroups/be554af1-2afa-4168-b64f-bdcb9ce7ac7b";
constexpr std::string_view kData="/data/hw201209/";
bool digits(std::string_view value) {
  return !value.empty() && std::all_of(value.begin(),value.end(),
      [](unsigned char c){return c>='0' && c<='9';});
}
bool storage_namespace(std::string_view file) {
  if(file.starts_with("slot")) {
    const auto slash=file.find('/');
    return slash!=std::string_view::npos && digits(file.substr(4,slash-4));
  }
  // TU46 writes dated backup blobs alongside its numbered save slots.
  return file.starts_with("backup/") && file.size()>18 &&
      file[11]=='/' && file[14]=='/' && file[17]=='/' &&
      digits(file.substr(7,4)) && digits(file.substr(12,2)) && digits(file.substr(15,2));
}
LocalResponse text(unsigned status,std::string value) {
  return {status,"application/json",{value.begin(),value.end()}};
}
std::string json_string(std::string_view value) {
  std::string out="\"";
  constexpr char hex[]="0123456789abcdef";
  for(unsigned char c:value) {
    if(c=='"' || c=='\\') { out+='\\'; out+=char(c); }
    else if(c<32) { out+="\\u00"; out+=hex[c>>4]; out+=hex[c&15]; }
    else out+=char(c);
  }
  return out+'"';
}
}

LocalTitleStorage::LocalTitleStorage(const std::filesystem::path& database)
    :store_(database),backup_(database.string()+".bak") {}

void LocalTitleStorage::backup() {
  const auto pending=std::filesystem::path(backup_.string()+".revision-"+std::to_string(store_.revision()));
  store_.backup(pending);
  if(!MoveFileExW(pending.c_str(),backup_.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))
    throw std::runtime_error("Could not replace title-storage backup atomically");
}

LocalResponse LocalTitleStorage::request(std::string_view method,std::string_view raw_path,
                                        std::span<const uint8_t> body) {
  std::scoped_lock lock(mutex_);
  auto path=std::string(raw_path.substr(0,raw_path.find('?')));
  while(path.starts_with("//")) path.erase(0,1);
  const auto user_end=path.find(')');
  if(!path.starts_with("/users/xuid(") || user_end==std::string::npos)
    return text(404,"{\"error\":\"unknown_route\"}");
  const auto user=path.substr(12,user_end-12);
  if(user!="2533274790395905" && user!="16140901064495857665")
    return text(403,"{\"error\":\"unknown_local_profile\"}");
  const auto suffix=std::string_view(path).substr(user_end+1);
  if(suffix=="/gamercard" && method=="GET") return text(200,"{\"tier\":\"Gold\"}");
  if(!suffix.starts_with(kGroup)) return text(404,"{\"error\":\"unknown_title_group\"}");
  auto records=store_.load();
  uint64_t used=0;
  for(const auto& entry:records) if(entry.key.starts_with("title-storage/")) used+=entry.bytes.size();
  auto relative=suffix.substr(kGroup.size());
  if((relative.empty() || relative=="/") && method=="GET") {
    return text(200,"{\"UsedBytesInVerifiedStorage\":"+std::to_string(used)+
      ",\"QuotaBytesForVerifiedStorage\":"+std::to_string(kQuota)+
      ",\"UsedBytesInUnverifiedStorage\":0,\"QuotaBytesForUnverifiedStorage\":"+std::to_string(kQuota)+"}");
  }
  if(!relative.starts_with(kData)) return text(404,"{\"error\":\"unknown_storage_path\"}");
  auto file=std::string(relative.substr(kData.size()));
  const bool binary=file.ends_with(",binary");
  if(binary) file.resize(file.size()-7);
  if(file.size()>512 || file.find("..")!=std::string::npos || file.find('\\')!=std::string::npos ||
      file.find('%')!=std::string::npos || !storage_namespace(file))
    return text(400,"{\"error\":\"invalid_blob_path\"}");
  const std::string key="title-storage/"+file;
  auto found=std::find_if(records.begin(),records.end(),[&](const auto& r){return r.key==key;});
  if(method=="GET" && binary) {
    if(found==records.end()) return text(404,"{\"error\":\"blob_not_found\"}");
    return {200,"application/octet-stream",found->bytes};
  }
  if(method=="GET") {
    std::string list="{\"blobs\":[";
    bool first=true;
    for(const auto& entry:records) {
      if(!entry.key.starts_with(key)) continue;
      if(!first) list+=',';
      first=false;
      const auto name=std::string_view(entry.key).substr(std::string_view("title-storage/").size());
      list+="{\"fileName\":"+json_string(name)+",\"size\":"+std::to_string(entry.bytes.size())+"}";
    }
    return text(200,list+"],\"pagingInfo\":{\"continuationToken\":\"\",\"totalItems\":"+std::to_string(std::count_if(records.begin(),records.end(),[&](const auto& entry){return entry.key.starts_with(key);}))+"}}");
  }
  if(method=="PUT" && binary) {
    const uint64_t previous=found==records.end()?0:found->bytes.size();
    if(body.size()>kQuota || used-previous+body.size()>kQuota) return text(507,"{\"error\":\"quota_exceeded\"}");
    const bool created=found==records.end();
    SaveRecord value{key,1,{body.begin(),body.end()}};
    if(created) records.push_back(std::move(value)); else *found=std::move(value);
    store_.save(records,store_.revision());
    backup();
    return text(201,"{}");
  }
  if(method=="DELETE" && binary) {
    if(found==records.end()) return text(404,"{\"error\":\"blob_not_found\"}");
    records.erase(found);
    store_.save(records,store_.revision());
    backup();
    return text(200,"{}");
  }
  return text(405,"{\"error\":\"unsupported_method\"}");
}
}
