import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MagicalImage } from "@/components/site/magical-image";

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-20">
        <div className="flex flex-col lg:flex-row items-center gap-12">
          {/* Left side - Image */}
          <div className="lg:w-1/2">
            <div className="rounded-lg shadow-2xl overflow-hidden">
              <MagicalImage
                src="/hogwarts-castle-at-dusk-mist-glowing-windows.jpg"
                alt="Hogwarts castle shrouded in mysterious mist"
                width={600}
                height={400}
              />
            </div>
          </div>

          {/* Right side - Login Form */}
          <div className="lg:w-1/2 w-full max-w-md">
            <Card className="bg-black/30 backdrop-blur-sm border-amber-500/30 shadow-2xl">
              <CardHeader className="text-center">
                <div className="mb-4">
                  <img
                    src="/hogwarts-crest-vintage-parchment.jpg"
                    alt="Hogwarts Crest"
                    className="w-20 h-20 mx-auto rounded-full border-2 border-amber-500"
                  />
                </div>
                <CardTitle className="text-2xl font-serif text-amber-300">
                  Forbidden Sections
                </CardTitle>
                <p className="text-amber-100/80 text-sm">
                  Only authorized personnel may enter these restricted areas
                </p>
              </CardHeader>

              <CardContent className="space-y-4">
                <form className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-amber-200">
                      Username
                    </Label>
                    <Input
                      id="username"
                      type="text"
                      placeholder="Enter your magical identifier"
                      className="bg-black/50 border-amber-500/50 text-amber-100 placeholder:text-amber-300/50 focus:border-amber-400"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-amber-200">
                      Password
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Speak the incantation"
                      className="bg-black/50 border-amber-500/50 text-amber-100 placeholder:text-amber-300/50 focus:border-amber-400"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-amber-600 hover:bg-amber-700 text-black font-semibold transition-all duration-300 transform hover:scale-105"
                  >
                    Enter the Forbidden Realm
                  </Button>
                </form>

                <div className="pt-4 border-t border-amber-500/30">
                  <p className="text-center text-amber-200/70 text-sm">
                    "It is our choices that show what we truly are, far more
                    than our abilities."
                  </p>
                  <p className="text-center text-amber-300/50 text-xs mt-1">
                    - Albus Dumbledore
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="mt-6 text-center">
              <p className="text-amber-200/60 text-sm">
                Warning: Unauthorized access to forbidden areas may result in
                detention with Professor Snape
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
