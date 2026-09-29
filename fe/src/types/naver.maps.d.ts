export {}; 

declare global {
  interface Window {
    naver: typeof naver;
  }

  namespace naver.maps {
    class LatLng {
      constructor(lat: number, lng: number);
      lat(): number;
      lng(): number;
    }

    class Map {
      constructor(container: string | HTMLElement, options: any);
      setCenter(latlng: LatLng): void;
      setZoom(zoom: number): void;
      getBounds(): any;
      getProjection(): any;
      addListener(event: string, handler: Function): void;
      panTo(latlng: LatLng): void;
    }

    class Icon {
      url: string;
      size?: Size;
      scaledSize?: Size;
      origin?: Point;
      anchor?: Point;
    }

    class Marker {
      private _animation: Animation | null; 
      private _position: LatLng; 

      constructor(options: { 
        position: LatLng; 
        map: Map;
        icon: Icon;
        animation?: Animation;
        name?: string;
        [key: string]: any; 
      }) {
        this._position = options.position;
        this._animation = options.animation ?? null;
        this.name = options.name ?? '';
      }

      setMap(map: Map | null): void {
        // Actual implementation
      }

      // Adding setAnimation method
      setAnimation(animation: Animation | null): void {
        this._animation = animation;
      }

      // Adding getAnimation method
      getAnimation(): Animation | null {
        return this._animation;
      }

      // Adding getPosition method
      getPosition(): LatLng {
        return this._position;
      }
    }

    enum Animation {
      BOUNCE = 1,
      DROP = 2
    }

    class Size {
      constructor(width: number, height: number);
    }

    class Point {
      constructor(x: number, y: number);
    }

    class Polyline {
      constructor(options: any);
      setMap(map: Map | null): void;
    }

    const Event: {
      addListener: (target: any, eventName: string, handler: Function) => void;
    };
  }
}
