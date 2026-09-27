"use client";
import { Banner } from "@/components/site/banner";
import { useState } from "react";

export default function ContactPage() {
  const [sent, setSent] = useState(false);

  return (
    <>
      <Banner
        title="Contact"
        subtitle="Send us an owl or use this Muggle-compatible form."
        imgAlt="Barn owl perched with letter"
        imgUrl="https://images.unsplash.com/photo-1465101046530-73398c7f28ca"
      />
      <div className="mx-auto max-w-3xl px-4 md:px-6 py-10 md:py-16">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSent(true);
          }}
          className="scroll-paper p-6 space-y-6"
          aria-labelledby="contact-title"
        >
          <h2 id="contact-title" className="font-serif text-2xl">
            Owl-Themed Contact
          </h2>
          <div>
            <label className="block text-sm mb-1">Your Name</label>
            <input
              className="w-full rounded-md border border-border bg-card px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Email</label>
            <input
              type="email"
              className="w-full rounded-md border border-border bg-card px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Message</label>
            <textarea
              rows={4}
              className="w-full rounded-md border border-border bg-card px-3 py-2"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-md bg-accent/20 hover:bg-accent/30 transition"
          >
            Send Owl
          </button>
          {sent ? (
            <p role="status" className="opacity-90">
              Your owl is on its way!
            </p>
          ) : null}
        </form>
      </div>
    </>
  );
}
