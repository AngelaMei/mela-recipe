// How a dish photo is framed on its plate.
//
// cx, cy: the point of the photo (0..1 of its width / height) that sits at the
//         centre of the dish.
// zoom:   1 = the photo's short side exactly spans the dish area; up to 4.
// aspect: the photo's width / height.

export interface PhotoCrop {
  cx: number;
  cy: number;
  zoom: number;
  aspect: number;
}

export const MIN_ZOOM = 1;
export const MAX_ZOOM = 3;

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/** Size of the photo, for a dish area that is `view` units across. */
export function imageSize(view: number, crop: Pick<PhotoCrop, "zoom" | "aspect">) {
  const short = view * crop.zoom;
  return crop.aspect >= 1 ? { w: short * crop.aspect, h: short } : { w: short, h: short / crop.aspect };
}

/** Keep the photo covering the whole dish area: no empty corners. */
export function clampCrop(crop: PhotoCrop): PhotoCrop {
  const zoom = clamp(crop.zoom, MIN_ZOOM, MAX_ZOOM);
  const { w, h } = imageSize(1, { zoom, aspect: crop.aspect });
  const hx = 0.5 / w;
  const hy = 0.5 / h;
  return { ...crop, zoom, cx: clamp(crop.cx, hx, 1 - hx), cy: clamp(crop.cy, hy, 1 - hy) };
}

export function centredCrop(aspect: number): PhotoCrop {
  return { cx: 0.5, cy: 0.5, zoom: 1, aspect };
}

/** Load an image just to learn its aspect ratio. */
export function loadAspect(url: string): Promise<number> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 1);
    img.onerror = () => resolve(1);
    img.src = url;
  });
}
