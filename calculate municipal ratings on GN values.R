# Variables:
#     origin.#X (Time taken to drive from origin road point to 1st nearest POI variable X (e.g. 1D))
#     origin.wpop (Population at origin point)
#     origin.wpopm (Population of municipality containing origin point)
#1. Load variables.
#2. Access as function of proportion of municipal population at each road node. wpopdt#X = #X * wpop
#3. Municipal pop-weighted access rating. dtX#m = sum(wpopdt#X)/wpopm

#1
originD <- read.csv('accD.csv')
origin <- read.csv('inOsnap.csv')
origin2 <- merge(x = origin, y = originD, by = "NN", all.x = TRUE)

#2
origin2$wpopdtD <- NA
origin2$wpopdtD <- with(origin2, X1D * wpop)

#3
D1m <- as.data.frame(xtabs(wpopdtD ~ xmid, origin2))
library(plyr)
D1m <- rename(D1m, c("Freq"="D1m"))
wpopm <- as.data.frame(xtabs(wpop ~ xmid, origin2))
wpopm <- rename(wpopm, c("Freq"="wpopm"))
D1m <- merge(x=D1m, y=wpopm, by="xmid")
D1m$dtD1m <- NA
D1m$dtD1m <- with(D1m, D1m / wpopm)
write.csv(D1m, file = "D1m.csv")
D1m <- rename(D1m, c("dtD1m"="D1")) # Decided post-run on this standardized variable name.


#1 Hospitals
H <- read.csv('accH.csv')
originH <- merge(x = origin, y = H, by = "NN", all.x = TRUE)

#2
originH$wpopdtH <- NA
originH$wpopdtH <- with(originH, X1H * wpop)

#3
H1m <- as.data.frame(xtabs(wpopdtH ~ xmid, originH))
H1m <- rename(H1m, c("Freq"="H1m"))
H1m <- merge(x=H1m, y=D1m, by="xmid")
H1m$H1 <- NA
H1m$H1 <- with(H1m, H1m / wpopm)
write.csv(H1m, file = "drivetime1.csv")


#1 Gas
G <- read.csv('accG.csv')
originG <- merge(x = origin, y = G, by = "NN", all.x = TRUE)

#2
originG$wpopdtG <- NA
originG$wpopdtG <- with(originG, X1G * wpop)

#3
G1m <- as.data.frame(xtabs(wpopdtG ~ xmid, originG))
G1m <- rename(G1m, c("Freq"="G1m"))
G1m <- merge(x=G1m, y=H1m, by="xmid")
G1m$G1 <- NA
G1m$G1 <- with(G1m, G1m / wpopm)
write.csv(G1m, file = "drivetime1.csv")



# Join with municipality names. (Later removed some of the unnecessary columns in Excel.)
munic <- read.csv("mid.csv")
drivetime <- merge(x = G1m, y = munic, by.x = "xmid", by.y = "mid")
write.csv(drivetime, file = "drivetime1.csv")