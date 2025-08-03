/* Guitar-MIDI Service Worker */

const CACHE_NAME = 'guitar-midi-v1.0.0';
const urlsToCache = [
  '/',
  '/instruments',
  '/presets',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/js/websocket.js',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Instalación del Service Worker
self.addEventListener('install', function(event) {
  console.log('🔧 Service Worker: Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('📦 Service Worker: Cache abierto');
        return cache.addAll(urlsToCache);
      })
      .catch(function(error) {
        console.error('❌ Service Worker: Error en instalación:', error);
      })
  );
  
  // Forzar activación inmediata
  self.skipWaiting();
});

// Activación del Service Worker
self.addEventListener('activate', function(event) {
  console.log('✅ Service Worker: Activando...');
  
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('🧹 Service Worker: Eliminando cache antigua:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Reclamar todos los clientes
  self.clients.claim();
});

// Intercepción de peticiones (estrategia Network First para APIs, Cache First para assets)
self.addEventListener('fetch', function(event) {
  const requestUrl = new URL(event.request.url);
  
  // Para APIs: Network First
  if (requestUrl.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          // Si la respuesta es exitosa, la guardamos en cache
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then(function(cache) {
                cache.put(event.request, responseClone);
              });
          }
          return response;
        })
        .catch(function() {
          // Si falla la red, intentamos servir desde cache
          return caches.match(event.request)
            .then(function(response) {
              if (response) {
                return response;
              }
              // Si no hay cache, devolvemos una respuesta de error
              return new Response(
                JSON.stringify({ error: 'Sin conexión y sin cache disponible' }),
                {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: new Headers({
                    'Content-Type': 'application/json'
                  })
                }
              );
            });
        })
    );
    return;
  }
  
  // Para assets estáticos: Cache First
  if (requestUrl.pathname.startsWith('/static/') || 
      requestUrl.pathname === '/' || 
      requestUrl.pathname === '/instruments' || 
      requestUrl.pathname === '/presets') {
    
    event.respondWith(
      caches.match(event.request)
        .then(function(response) {
          // Si está en cache, lo devolvemos
          if (response) {
            return response;
          }
          
          // Si no está en cache, lo buscamos en la red
          return fetch(event.request)
            .then(function(response) {
              // Verificar si la respuesta es válida
              if (!response || response.status !== 200 || response.type !== 'basic') {
                return response;
              }
              
              // Clonar la respuesta para cache
              const responseToCache = response.clone();
              
              caches.open(CACHE_NAME)
                .then(function(cache) {
                  cache.put(event.request, responseToCache);
                });
              
              return response;
            });
        })
    );
    return;
  }
  
  // Para todo lo demás: Network Only
  event.respondWith(fetch(event.request));
});

// Manejar actualizaciones
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('🔄 Service Worker: Actualizando...');
    self.skipWaiting();
  }
});

// Manejar sincronización en segundo plano
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    console.log('🔄 Service Worker: Sincronización en segundo plano');
    event.waitUntil(doBackgroundSync());
  }
});

// Función de sincronización en segundo plano
function doBackgroundSync() {
  // Aquí podríamos implementar lógica para sincronizar 
  // cambios pendientes cuando se recupere la conexión
  return Promise.resolve();
}

// Notificaciones push (para futuras mejoras)
self.addEventListener('push', function(event) {
  if (event.data) {
    const options = {
      body: event.data.text(),
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-96x96.png',
      vibrate: [100, 50, 100],
      data: {
        url: '/'
      },
      actions: [
        {
          action: 'view',
          title: 'Ver',
          icon: '/static/icons/icon-96x96.png'
        },
        {
          action: 'dismiss',
          title: 'Descartar'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification('Guitar-MIDI', options)
    );
  }
});

// Manejar click en notificaciones
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  }
});

// Logs para debug
console.log('🎸 Guitar-MIDI Service Worker cargado');
console.log('📝 Cache name:', CACHE_NAME);
console.log('📦 URLs en cache:', urlsToCache);