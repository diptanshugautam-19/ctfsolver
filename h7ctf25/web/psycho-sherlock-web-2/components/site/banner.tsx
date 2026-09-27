import Image from "next/image";
import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  imgAlt: string;
  imgUrl: string;
  children?: ReactNode;
};

export function Banner({ title, subtitle, imgAlt, imgUrl, children }: Props) {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="absolute inset-0">
        <Image
          src={
            imgUrl ||
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb"
          }
          alt={imgAlt}
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/50 to-background/40" />
      </div>
      <div className="relative mx-auto max-w-6xl px-4 md:px-6 py-20 md:py-28">
        <h1 className="font-serif text-balance text-3xl md:text-5xl text-white drop-shadow-lg">
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-3 max-w-2xl text-pretty text-white/90 leading-relaxed">
            {subtitle}
          </p>
        ) : null}
        {children ? <div className="mt-6">{children}</div> : null}
      </div>
    </section>
  );
}
