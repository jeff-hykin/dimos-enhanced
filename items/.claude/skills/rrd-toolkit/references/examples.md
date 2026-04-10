# Worked Examples

## 1. Explore a new recording
```sh
rrd-info file.rrd                     # metadata + timeline overview
rrd-entities file.rrd                 # what's in it
rrd-rate file.rrd                     # rates for all entities
rrd-tf file.rrd                       # transform tree
rrd-warnings file.rrd                 # any logged warnings
```

## 2. "Is odom publishing consistently?"
```sh
rrd-rate file.rrd --entity /world/corrected_odometry
rrd-gaps file.rrd --entity /world/corrected_odometry --threshold 0.2
```

## 3. "Point cloud size at every frame"
```sh
rrd-summary file.rrd --entity /world/lidar --component Points3D:positions
```
Returns an array of `{time, size}` records plus overall stats.

## 4. "When did the robot get within 1m of (0, 2, 6)?"
```sh
rrd-near-point file.rrd \
    --entity /world/corrected_odometry \
    --component Transform3D:translation \
    --point 0,2,6 --radius 1.0
```

## 5. "How big was the lidar point cloud at those moments?"
```sh
rrd-correlate file.rrd \
    --entity-a /world/corrected_odometry --component-a Transform3D:translation \
    --when-a 'norm(value - [0,2,6]) < 1.0' \
    --entity-b /world/lidar --component-b Points3D:positions
```

## 6. "Resample odom at 10Hz for the first 10 seconds"
```sh
rrd-sample file.rrd --entity /world/corrected_odometry --hz 10 --values |
    jq '{samples: [.samples[] | select(.sample_time < .samples[0].sample_time + 10)]}'
```
Or more simply use `rrd-slice` and `rrd-sample` together.

## 7. "First 2 seconds of lidar"
```sh
rrd-head file.rrd --entity /world/lidar --seconds 2.0 --summary
```

## 8. "What was published right after the warning?"
```sh
rrd-warnings file.rrd
# copy the time of interest, then
rrd-at file.rrd --entity /world/corrected_odometry --time 1234567.89 -n 5
```

## 9. "Biggest point clouds in the recording"
```sh
rrd-when file.rrd \
    --entity /world/lidar \
    --component Points3D:positions \
    --predicate 'size > 50000'
```

## 10. "Distribution of robot heights (Z)"
```sh
rrd-histogram file.rrd \
    --entity /world/corrected_odometry \
    --component Transform3D:translation \
    --field z --bins 30
```
