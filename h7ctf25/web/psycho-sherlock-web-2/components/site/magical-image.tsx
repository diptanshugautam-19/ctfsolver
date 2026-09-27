import Image from "next/image";

type Props = {
  src: string;
  alt: string;
  width: number;
  height: number;
};

export function MagicalImage({ src, alt, width, height }: Props) {
  return (
    <div className="magical-float">
      <div className="framed-img overflow-hidden">
        <Image
          src={
            src ||
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb"
          }
          alt={alt}
          width={width}
          height={height}
          className="object-cover w-full h-auto"
        />
      </div>
    </div>
  );
}
