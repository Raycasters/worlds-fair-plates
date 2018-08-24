Vue.use(VTooltip);

let data = null;
let scroller;

document.addEventListener('DOMContentLoaded', () => {}, false);

function map(n, start1, stop1, start2, stop2, withinBounds) {
  var newval = (n - start1) / (stop1 - start1) * (stop2 - start2) + start2;
  if (!withinBounds) {
    return newval;
  }
  if (start2 < stop2) {
    return this.constrain(newval, start2, stop2);
  } else {
    return this.constrain(newval, stop2, start2);
  }
}

function imageUrl(listing) {
  return 'static/' + listing.image.replace('listing_images/', '');
}

function thumbnail(listing) {
  return 'static/' + listing.image.replace('listing_images/', '') + '.thumb.jpg';
}

const Home = {
  template: '#home',
  delimiters: ['${', '}'],
  data: function() {
    return {
      plates: [],
      listings: [],
      plate: null,
      loading: false,
      scroll: 0,
      rightArrowOpacity: 1,
    };
  },

  created: function() {
    this.loadPlates();
  },

  mounted: function(){
    scroller = new SweetScroll(
      {
        vertical: false,
        horizontal: true
      },
      '.plate-container'
    );
  },

  updated: function() {
    scroller = new SweetScroll(
      {
        vertical: false,
        horizontal: true
      },
      '.plate-container'
    );
  },

  methods: {
    loadPlates: function() {
      if (data) {
        if (this.plates.length == 0) this.plates = data;
        return true;
      }

      this.loading = true;
      fetch('/plates?listings=true&listing_limit=500')
        .then(response => {
          return response.json();
        })
        .then(json => {
          this.plates = json;
          data = json;
          this.loading = false;
          scroller = new SweetScroll(
            {
              vertical: true,
              horizontal: true
            },
            '.plate-container'
          );
        })
        .catch(ex => {
          console.log('parsing failed', ex);
        });
    },

    imageUrl: imageUrl,
    thumbnail: thumbnail,

    listStyle: function(listing) {
      if (this.showMap) {
        //50, -125
        //21, 65
        // let x = map(listing.lng, -180, 180, 0, 100);
        // let y = map(listing.lat, -90, 90, 0, 100);
        let x = map(listing.lng, -125, 50, 0, 1000);
        let y = map(listing.lat, 21, 50, 1000, 0);
        // let x = (listing.lng * 1000)/360;
        // let y = (listing.lat * 1000)/180;
        let style = {
          // position: 'absolute',
          // left: `${x}%`,
          // top: `${y}%`,
          transform: `translate(${x}px, ${y}px)`
          // width: '20px',
          // display: listing.lat ? 'block' : 'none',
          // border: '1px solid #000',
        };
        console.log(style);
        return style;
      } else {
        return {};
      }
    },

    startHover: function(e) {
      e.target.play();
      // e.target.loop();
    },

    endHover: function(e) {
      e.target.pause();
      e.target.currentTime = 0;
    },

    goLeft: function(e) {
      e.preventDefault();
      let el = document.querySelector('.plate-container');
      scroller.to('-=' + el.clientWidth);
    },

    goRight: function(e) {
      e.preventDefault();
      let el = document.querySelector('.plate-container');
      scroller.to('+=' + el.clientWidth);
    },

    changeScroll: function(e) {
      this.scroll = e.target.scrollLeft;
      this.rightArrowOpacity = e.target.scrollLeft < e.target.scrollWidth - e.target.clientWidth ? 1 : 0.0;
    }
  }
};

const MapPage = {
  template: '#map-page',
  delimiters: ['${', '}'],
  data: function() {
    return {
      plates: [],
      plate: null,
      listings: [],
      loading: false,
      accessToken: "pk.eyJ1IjoienNjaG5laWRlciIsImEiOiJjaXg3eWUzeGowMXEyMnlxeWI1MzBudzN0In0.i-aef9w2ifwlPvXerrQOwA",
      mapStyle: "MAP_STYLE", // your map style
      selected: null,
      scroll: 0,
      downArrowOpacity: 1
    };
  },

  created: function() {
    this.loadPlates();
  },

  mounted: function() {
    this.makeMap();
  },

  methods: {
    loadPlates: function() {
      console.log('loading');
      if (data) {
        if (this.plates.length == 0) this.plates = data;
        this.setListings();
        return true;
      }

      this.loading = true;
      fetch('/plates?listings=true&listing_limit=1000')
        .then(response => {
          return response.json();
        })
        .then(json => {
          this.plates = json;
          data = json;
          this.setListings();
          this.loading = false;
          console.log('loaded');
        })
        .catch(ex => {
          console.log('parsing failed', ex);
        });
    },

    showPlate: function(plateID) {
      this.selected = plateID;
      let allListings = document.querySelectorAll('.marker');
      let listings = document.querySelectorAll('.marker-' + plateID);
      for (let i = 0; i < allListings.length; i++) {
        allListings[i].classList.remove('selected');
      }
      for (let i = 0; i < listings.length; i++) {
        listings[i].classList.add('selected');
      }
    },

    viewAll: function(e) {
      e.preventDefault();
      this.selected = null;
      let allListings = document.querySelectorAll('.marker');
      for (let i = 0; i < allListings.length; i++) {
        allListings[i].classList.add('selected');
      }
    },

    onScroll: function(e) {
      this.scroll = e.target.scrollTop;
      this.downArrowOpacity = e.target.scrollTop < e.target.scrollHeight - e.target.clientHeight ? 1 : 0.0;
    },

    goUp: function(e) {
      e.preventDefault();
      let scroll = new SweetScroll(
        {
          vertical: true,
          horizontal: false
        },
        '.map-plates'
      );
      scroll.to('-=' + document.querySelector('.map-plates').clientHeight);
    },

    goDown: function(e) {
      e.preventDefault();
      let scroll = new SweetScroll(
        {
          vertical: true,
          horizontal: false
        },
        '.map-plates'
      );
      scroll.to('+=' + document.querySelector('.map-plates').clientHeight);
    },

    setListings: function() {
      let listings = this.plates.map(p => p.listings);
      listings = [].concat.apply([], listings);
      this.listings = listings;

      let addToMap = () => {
        if (this.mapbox) {
          listings.forEach((l) => {
            var el = document.createElement('img');
            el.classList.add('marker');
            el.classList.add('selected');
            el.classList.add('marker-' + l.plate_id);
            el.src = this.thumbnail(l);
            // el.addEventListener('click', (e) => {
            //   console.log(e);
            // });

            // make a marker for each feature and add to the map
            new mapboxgl.Marker(el)
              .setLngLat([l.lng, l.lat])
              .setPopup(new mapboxgl.Popup({ offset: 25 }) // add popups
              .setHTML('<h3>' + l.title + '</h3><p>' + l.location + '</p><p><a href="'+l.listing_url+'" target="blank">Original listing</a></p>'))
              .addTo(this.mapbox);

          });
        } else {
          setTimeout(addToMap, 200);
        }
      }
      let timer = setTimeout(addToMap, 200);
    },

    makeMap: function() {
      mapboxgl.accessToken = this.accessToken;
      this.mapbox = new mapboxgl.Map({
        container: 'map-container',
        style: 'mapbox://styles/zschneider/cj9ndjfuz3dhi2rthgplijv36',
        center: [-96, 37.8],
        zoom: 3
      });
    },

    imageUrl: imageUrl,
    thumbnail: thumbnail,
  },

  computed: {
    upArrowOpacity: function() {
      return this.scroll > 0 ? 1 : 0.0;
    },
  }


};

const PlatePage = {
  template: '#plate-page',
  delimiters: ['${', '}'],

  data: function() {
    return {
      listings: [],
      id: null,
      title: '',
      description: '',
      image: '',
      nextPlate: 1,
      prevPlate: 1,
      rotation: {x: 0, y: 0, z: 0},
      speed: 0.001,
      userControl: false,
      admin: window.admin,
      allPlates: [],
      loaded: false,
      lightIntensity: 0.8
    };
  },

  watch: {
    '$route': function(to, from) {
      window.cancelAnimationFrame(this.animationFrame);
      this.loaded = false;
      this.image = '';
      this.loadPlate();
      this.getNextPrev();
      this.rotation = {x: 0, y: 0, z: 0};
      this.speed = 0.001;
      this.userControl = false;
    }
  },

  created: function() {
    this.loadPlate();
    this.loadPlates();
  },

  methods: {
    loadPlate: function() {
      this.loaded = false;

      fetch('/plates/' + this.$route.params.id)
        .then(response => {
          return response.json();
        })
        .then(json => {
          this.listings = json.listings;
          this.id = json.id;
          this.title = json.title;
          this.description = json.description;
          this.image = json.image;
          this.lightIntensity = json.intensity;
          this.loaded = true;
        })
        .catch(ex => {
          console.log('parsing failed', ex);
        });
    },

    loadPlates: function() {
      if (data) {
        if (this.allPlates.length == 0) this.allPlates = data;
        this.getNextPrev();
        return true;
      }

      // this.loading = true;
      fetch('/plates?listings=true&listing_limit=500')
        .then(response => {
          return response.json();
        })
        .then(json => {
          this.allPlates = json;
          data = json;
          this.getNextPrev();
        })
        .catch(ex => {
          console.log('parsing failed', ex);
        });
    },

    getNextPrev: function() {
      let ids = this.allPlates.map(p => p.id);
      let currentIndex = ids.indexOf(parseInt(this.$route.params.id));
      // console.log(this.$route.params.id)
      let nextIndex = currentIndex + 1;
      if (nextIndex >= ids.length) nextIndex = 0;

      let prevIndex = currentIndex - 1;
      if (prevIndex < 0) prevIndex = ids.length-1;

      // console.log(ids)
      // console.log(nextIndex, prevIndex)
      
      this.nextPlate = ids[nextIndex];
      this.prevPlate = ids[prevIndex];
    },

    goLeft: function(e){
      
    },

    goRight: function(e) {

    },

    onLoad: function() {
      this.rotate();
    },

    toggleControl: function() {
      this.userControl = true;
    },

    rotate: function () {
      if (this.userControl) return false;

      this.rotation.y += this.speed;
      if (this.rotation.y > .5 || this.rotation.y < -.5){
        this.speed *= -1;
      }
      this.animationFrame = requestAnimationFrame( this.rotate );
    },

    imageUrl: imageUrl,
    thumbnail: thumbnail
  }
};

const NotPlates = {
  template: '#not-plates',
  delimiters: ['${', '}'],
  data: function() {
    return {
      listings: []
    };
  },

  created: function() {
    this.loadListings();
  },

  methods: {
    loadListings() {
      fetch('/listings?notplates=true')
        .then(response => {
          return response.json();
        })
        .then(json => {
          this.listings = json;
        })
        .catch(ex => {
          console.log('parsing failed', ex);
        });
    },
    thumbnail: thumbnail
  }
};

const Plate = {
  template: '#plate',
  delimiters: ['${', '}']
};

const Listing = {
  template: '#listing',
  delimiters: ['${', '}']
};

const Welcome = {
  template: '#welcome',
  delimiters: ['${', '}'],
  data: function() {
    return {
      rotation: {x: 0, y: 0, z: 0},
      speed: 0.0015,
      userControl: false,
    }
  },
  methods: {
    onLoad: function() {
      this.rotate();
    },
    toggleControl: function() {
      this.userControl = true;
    },
    rotate: function () {
      if (this.userControl) return false;

      this.rotation.y += this.speed;
      if (this.rotation.y > .5 || this.rotation.y < -.5){
        this.speed *= -1;
      }
      requestAnimationFrame( this.rotate );
    }
  }
};

const Info = {
  template: '#info',
  delimiters: ['${', '}']
};

const routes = [
  {
    path: '/',
    component: Welcome
  },
  {
    path: '/plates',
    name: 'plates',
    component: Home
  },
  {
    path: '/map',
    name: 'map-page',
    component: MapPage
  },
  {
    path: '/info',
    name: 'info',
    component: Info
  },
  {
    path: '/notplates',
    name: 'not-plates',
    component: NotPlates
  },
  {
    path: '/plate/:id',
    name: 'plate-page',
    component: PlatePage
  },
  {
    path: '/listing/:id',
    name: 'listing',
    component: Listing
  }
];

const router = new VueRouter({
  routes: routes,
});

new Vue({
  router,
  el: '#app',
  delimiters: ['${', '}'],
  data: {}
});
