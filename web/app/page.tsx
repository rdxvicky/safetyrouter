import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { ProvidersStrip } from "./components/ProvidersStrip";
import { HowItWorks } from "./components/HowItWorks";
import { CrisisSafety } from "./components/CrisisSafety";
import { RoutingTable } from "./components/RoutingTable";
import { Documentation } from "./components/Documentation";
import { Features } from "./components/Features";
import { Configuration } from "./components/Configuration";
import { InstallCTA } from "./components/InstallCTA";
import { Changelog } from "./components/Changelog";
import { Footer } from "./components/Footer";

export default function Page() {
  return (
    <>
      <Nav />
      <Hero />
      <ProvidersStrip />
      <HowItWorks />
      <CrisisSafety />
      <RoutingTable />
      <Documentation />
      <Features />
      <Configuration />
      <InstallCTA />
      <Changelog />
      <Footer />
    </>
  );
}
