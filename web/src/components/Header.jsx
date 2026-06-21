import { LighthouseIcon, ShieldIcon } from "./Icons.jsx";
import { PERSON_NAME } from "../data/fakeData.js";

// Top banner. Warm, reassuring, names the person so the family knows exactly who this is for.
export default function Header() {
  return (
    <header className="bg-blue-900 text-white">
      <div className="mx-auto flex max-w-4xl items-center gap-4 px-6 py-6">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-blue-700">
          <LighthouseIcon className="h-8 w-8" title="Lighthouse" />
        </div>
        <div className="flex-1">
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
            Lighthouse
          </h1>
          <p className="text-lg text-blue-100">
            Watching out for {PERSON_NAME}
          </p>
        </div>
        <div className="hidden items-center gap-2 rounded-full bg-green-600 px-4 py-2 text-base font-semibold sm:flex">
          <ShieldIcon className="h-5 w-5" />
          Protected
        </div>
      </div>
    </header>
  );
}
