<template>
    <div class="welcome-panel">
        <img :src="imageSrc" alt="script server logo">
        <div class="welcome-text">
            Welcome to the Script Server. <br> To start, select one of the scripts
        </div>
        <div class="welcome-cookie-text" ref="welcomeCookieText">
            or just take a cookie and enjoy!
        </div>
    </div>
</template>

<script>
import ConsoleImage from '@/assets/console.png'
import CookieImage from '@/assets/cookie.png'
import {mapActions} from 'vuex';

const defaultImageSrc = ConsoleImage;
const cookieImageSrc = CookieImage;

export default {
  name: 'AppWelcomePanel',
  data() {
    return {
      'imageSrc': defaultImageSrc
    }
  },

  methods: {
    ...mapActions('page', ['setLoading'])
  },

  mounted: function () {
    const welcomeCookiePanel = this.$refs.welcomeCookieText;
    welcomeCookiePanel.addEventListener('mouseover', () => {
      this.imageSrc = cookieImageSrc;
            });

            welcomeCookiePanel.addEventListener('mouseout', () => {
                this.imageSrc = defaultImageSrc;
            });

            this.setLoading(false);
        }

    }
</script>

<style scoped>
    .welcome-panel {
      flex: 1;
      color: var(--font-color-medium);
      display: flex;
      text-align: center;
      flex-direction: column;
      justify-content: center;
      align-items: center;

      height: 100%;
      overflow: hidden;
    }

    .welcome-text {
        margin-top: 15px;
    }

    .welcome-cookie-text {
        margin-top: 8px;
    }
</style>