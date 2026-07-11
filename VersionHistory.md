# Version History
---
**How Versioning works:**  
Vx.y.z  
x -> Major version. Such as a new addition. 0 means beta.  
y -> Minor version. Such as new addition to existing version.  
z -> Bugfix.  

---

V0.0.0 -> Inital release. Has functions to download videos and playlists. Also allows the user to download individual videos.
V0.0.1 -> Added health checks to the server.
V0.0.2 -> Fixed a bug where the docker container would look unhealthy.
V0.0.3 -> Installed deno to the container to allow yt-dlp to run as intended.
V0.0.4 -> Fixed some bugs. Prepared backend for next version. --WARNING--: Not compatible with older versions. You need to delete config folder in order for this version to work properly. This will reset users/downloaded videos but will not delete already downloaded videos.
V0.0.5 -> Fixed some bugs.
V0.0.6 -> Added per file moving to playlists.