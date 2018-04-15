import json
import matplotlib.pyplot as plt
import requests as r

text = open("Surface.txt", 'r').read()
data = json.loads(text)
# print(data["segments"])
start_times = []
loudnesses = []
durations = []
beat_times = []
beat_length = []
# print(data.keys())
# print(data["bars"])
for segment in data["segments"]:
    # print(segment["start"], segment["duration"], segment["loudness_start"])
    start_times.append(segment["start"]+3)
    durations.append(segment["duration"])
    loudnesses.append(abs(segment["loudness_max"]))
    # beat_times.append(segment[])

# for beat in data["beats"]:
#     if beat["confidence"] > 0:
#
#         beat_times.append(beat["start"])
#         beat_length.append(beat["duration"])

# plt.axis([0, 200, 0, 2])
# plt.ion()
# for i in range(24, len(beat_times)):
#     plt.scatter(beat_times[i], beat_length[i])
#     plt.pause(beat_length[i])

# plt.plot(start_times[:], loudnesses[:])
# plt.show()

plt.axis([0, 200, 0, 30])
plt.ion()
for i in range(0, len(durations)):
    print(durations[i])
    plt.scatter(start_times[i], loudnesses[i])
    plt.pause(durations[i])

# Dynamically graph song waveform