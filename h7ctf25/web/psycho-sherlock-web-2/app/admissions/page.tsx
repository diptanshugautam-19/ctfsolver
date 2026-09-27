"use client"
import { Banner } from "@/components/site/banner"
import { useState } from "react"

export default function AdmissionsPage() {
  const [status, setStatus] = useState<string | null>(null)

  return (
    <>
      <Banner
        title="Admissions"
        subtitle="First-years receive their letter via owl post by mid-summer. Submit your details below."
        imgAlt="Owl flying with letter under moonlight"
        imgUrl="/owl-post-letter-moonlight.jpg"
      />
      <div className="mx-auto max-w-3xl px-4 md:px-6 py-10 md:py-16">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            setStatus("Your owl has been dispatched. Please await confirmation.")
          }}
          className="space-y-6 scroll-paper p-6"
          aria-labelledby="admissions-title"
        >
          <h2 id="admissions-title" className="font-serif text-2xl">
            Owl-Post Application
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1">First name</label>
              <input className="w-full rounded-md border border-border bg-card px-3 py-2" required />
            </div>
            <div>
              <label className="block text-sm mb-1">Last name</label>
              <input className="w-full rounded-md border border-border bg-card px-3 py-2" required />
            </div>
          </div>
          <div>
            <label className="block text-sm mb-1">Email (for Muggle correspondence)</label>
            <input type="email" className="w-full rounded-md border border-border bg-card px-3 py-2" required />
          </div>
          <div>
            <label className="block text-sm mb-1">Address</label>
            <textarea className="w-full rounded-md border border-border bg-card px-3 py-2" rows={3} />
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" className="px-4 py-2 rounded-md bg-primary/30 hover:bg-primary/40 transition">
              Send by Owl
            </button>
            {status ? (
              <p role="status" className="opacity-90">
                {status}
              </p>
            ) : null}
          </div>
        </form>
      </div>
    </>
  )
}
