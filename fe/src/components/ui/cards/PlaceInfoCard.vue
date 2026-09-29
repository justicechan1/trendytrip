<template>
    <div class="small_pop" v-if="place">
        <header>
            <div class="header-title">
              <a :href="'https://www.instagram.com/explore/search/keyword/?q=' + encodeURIComponent(place.name)" 
                target="_blank" 
                id="instagram_link" >
                <img src="@/assets/instagram.png" alt="Instagram" id="instagram_img" />
              </a>
              <h3>{{ place.name }}</h3>
              <p>{{ place.category }}</p>
            </div>
            <p>{{ place.address }}</p>
             <p id="place_convenience" style="color: gray"> {{ place.conveniences.join(', ') }}</p>
        </header>
        <article>
            <div class="masonry-wrapper" v-if="place.images.length">
              <div class="masonry">
                <img
                  v-for="(image, index) in place.images"
                  :key="index"
                  :src="image"
                  :alt="`Image ${index + 1}`"
                  class="masonry-image"
                />
              </div>
            </div>
        </article>
        <footer>
            <button class="button-add" @click="addPlace">추가➕</button>
            <button class="button-close" @click="$emit('close')">닫기❌</button>
        </footer>   
    </div>
</template>

<script>
  export default {
    name: 'PlacePop',
    props:{
      place: {
        type: Object,
        required: true
      }
    },
    methods: {
      addPlace() {
        this.$emit('open-add-place');
      }
    }
  }
</script>

<style scoped>
.small_pop {
  position: absolute;
  top: 0;
  left: calc(100% + 10px);
  width: 20vw;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 12px;
  box-shadow: 0 4px 5px skyblue;
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-title h3 {
  font-size: 1.3rem;
  margin-bottom: 4px;
}

.header-title p {
  position: absolute;
  top: 0;
  right: 0;
  background-color: skyblue;
  color: white;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.9rem;
  margin: 20px;
}

#instagram_link {
  display: inline-block;
  cursor: pointer;
}

#instagram_img {
  width: 40px;
  height: 40px;
  margin: 0;
}

article {
  flex: 1 0 auto;
  display: flex;
  max-height: 15vw;
  flex-direction: column;
  align-items: center;
  overflow: auto;
} 

.masonry-wrapper {
  column-count: 2; /* 열 개수 */
  column-gap: 4px;
  width: 100%;
}

.masonry-image {
  width: 100%;
  height: auto;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

@media (max-width: 400px) {
  .masonry-feed {
    column-count: 2;
  }
}
@media (max-width: 200px) {
  .masonry-feed {
    column-count: 1;
  }
}

footer {
  margin-top: auto;
  display: flex;
  gap: 12px;
}

.button-add,
.button-close {
  flex: 1;
  padding: 10px 0;
  font-size: 0.95rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.button-add {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.button-add:hover {
  background-color: #c8e6c9;
}

.button-close {
  background-color: #fbe9e7;
  color: #c62828;
}

.button-close:hover {
  background-color: #ffcdd2;
}

</style>