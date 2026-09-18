<template>
  <div id="app">
    <div class="background-container">
      <div class="left-panel">
        <h1 class="system-title">Smart Sign Language Translation System</h1>
        <p class="system-description">
          This system achieves a real-time, contactless and robust "sign-to-speech"
          functionality, by integrating a high-performance polymer-based
          pyroelectric sensor array and artificial intelligence. It distinguishes
          multiple words, phrases and continuous sentences, similar signs with
          identical hand gestures but different body expressions, and operates
          reliably in both bright and dark conditions.
        </p>
      </div>

      <div class="right-panel">
        <div v-if="currentMapping" class="prediction-container">
          <p class="prediction-text">{{ currentMapping.text }}</p>
          <video
            v-if="currentMapping.video"
            :key="prediction"
            ref="predictionVideo"
            :src="currentMapping.video"
            class="prediction-video"
            autoplay
            muted
            playsinline
          ></video>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

const API_BASE_URL = process.env.VUE_APP_API_URL || "http://127.0.0.1:8000";

export default {
  name: "App",
  data() {
    return {
      prediction: "",
      isPredicting: false,
      activeAudio: null,
      mappings: {
        Can: {
          text: "Can",
          video: require("./assets/videos/1_Can.mp4"),
          sound: require("./assets/sounds/can.mp3"),
        },
        DontKnow: {
          text: "Don't Know",
          video: require("./assets/videos/2_DontKnow.mp4"),
          sound: require("./assets/sounds/don't know.mp3"),
        },
        Goodbye: {
          text: "Goodbye",
          video: require("./assets/videos/3_Goodbye.mp4"),
          sound: require("./assets/sounds/goodbye.mp3"),
        },
        Help: {
          text: "Help",
          video: require("./assets/videos/4_Help.mp4"),
          sound: require("./assets/sounds/help.mp3"),
        },
        How: {
          text: "How",
          video: require("./assets/videos/5_How.mp4"),
          sound: require("./assets/sounds/how.mp3"),
        },
        I: {
          text: "I",
          video: require("./assets/videos/6_I.mp4"),
          sound: require("./assets/sounds/I.mp3"),
        },
        Know: {
          text: "Know",
          video: require("./assets/videos/7_Know.mp4"),
          sound: require("./assets/sounds/know.mp3"),
        },
        No: {
          text: "No",
          video: require("./assets/videos/8_No.mp4"),
          sound: require("./assets/sounds/no.mp3"),
        },
        Please: {
          text: "Please",
          video: require("./assets/videos/9_Please.mp4"),
          sound: require("./assets/sounds/please.mp3"),
        },
        Sorry: {
          text: "Sorry",
          video: require("./assets/videos/10_Sorry.mp4"),
          sound: require("./assets/sounds/sorry.mp3"),
        },
        "Thank you": {
          text: "Thank you",
          video: require("./assets/videos/11-Thank you.mp4"),
          sound: require("./assets/sounds/thank you.mp3"),
        },
        What: {
          text: "What",
          video: require("./assets/videos/12_What.mp4"),
          sound: require("./assets/sounds/what.mp3"),
        },
        Yes: {
          text: "Yes",
          video: require("./assets/videos/13_Yes.mp4"),
          sound: require("./assets/sounds/yes.mp3"),
        },
        You: {
          text: "You",
          video: require("./assets/videos/14_You.mp4"),
          sound: require("./assets/sounds/you.mp3"),
        },
      },
    };
  },
  computed: {
    currentMapping() {
      if (!this.prediction) return null;
      return this.mappings[this.prediction] || {
        text: this.prediction,
        video: null,
        sound: null,
      };
    },
  },
  mounted() {
    window.addEventListener("keydown", this.handleKeyDown);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeyDown);
    this.stopAudio();
  },
  methods: {
    handleKeyDown(event) {
      if (event.code !== "Space" && event.key.toLowerCase() !== "s") return;
      event.preventDefault();
      this.startRecognition();
    },
    async startRecognition() {
      if (this.isPredicting) return;

      this.isPredicting = true;
      try {
        const response = await axios.post(
          `${API_BASE_URL}/capture-predict`,
          {},
          { timeout: 15000 }
        );
        this.prediction = response.data.prediction;
        this.playCurrentMedia();
      } catch (error) {
        console.error("Recognition failed:", error);
      } finally {
        this.isPredicting = false;
      }
    },
    playCurrentMedia() {
      this.$nextTick(() => {
        const video = this.$refs.predictionVideo;
        if (video) {
          video.currentTime = 0;
          video.play().catch(() => {});
        }
      });

      this.stopAudio();
      if (!this.currentMapping || !this.currentMapping.sound) return;

      this.activeAudio = new Audio(this.currentMapping.sound);
      this.activeAudio.play().catch(() => {});
    },
    stopAudio() {
      if (!this.activeAudio) return;
      this.activeAudio.pause();
      this.activeAudio.currentTime = 0;
      this.activeAudio = null;
    },
  },
};
</script>

<style>
body,
html {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

#app {
  font-family: Arial, sans-serif;
  height: 100%;
}

.background-container {
  background-color: #fff;
  height: 100%;
  display: flex;
  flex-direction: row;
}

.left-panel {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.right-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-title {
  font-size: 3em;
  color: #000;
  text-align: center;
  margin-bottom: 20px;
  font-weight: bold;
}

.system-description {
  font-size: 2em;
  color: #000;
  text-align: center;
  line-height: 1.6;
  font-weight: bold;
}

.prediction-container {
  text-align: center;
}

.prediction-text {
  font-size: 4em;
  color: #000;
  margin-bottom: 20px;
}

.prediction-video {
  width: 600px;
  height: auto;
}
</style>
