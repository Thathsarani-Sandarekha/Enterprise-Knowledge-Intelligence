"use client";

import { useEffect, useState } from "react";
import {
  ArrowRight, BookOpenText, Building2, ChevronDown, CircleAlert, FileStack,
  LayoutDashboard, LockKeyhole, Search, ShieldCheck, Sparkles, Stars,
} from "lucide-react";
import { KnowledgeSearch } from "@/components/knowledge-search";
import { DocumentLibrary } from "@/components/document-library";
import type { DemoUser } from "@/lib/api";

type Tab = "search" | "library";
const USERS: { id: DemoUser; label: string; subtitle: string }[] = [
  { id: "aster-admin", label: "Studio administrator", subtitle: "Asteria · All documents" },
  { id: "aster-procurement", label: "Procurement specialist", subtitle: "Asteria · Supplier quotes" },
  { id: "aster-designer", label: "Interior designer", subtitle: "Asteria · Design records" },
  { id: "aster-pm", label: "Project manager", subtitle: "Asteria · Project files" },
  { id: "rival-designer", label: "Other firm designer", subtitle: "Separate fictional tenant" },
  { id: "rival-admin", label: "Other firm admin", subtitle: "Separate fictional tenant" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("search");
  const [user, setUser] = useState<DemoUser>("aster-procurement");
  const [mobileNav, setMobileNav] = useState(false);
  const selected = USERS.find((option) => option.id === user)!;

  useEffect(() => { document.title = "Asteria | Knowledge Intelligence"; }, []);

  return (
    <div className="shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Building2 size={23} strokeWidth={1.6} /></div>
          <div><div className="brand-name">ASTERIA<span> / </span>STUDIO</div><div className="brand-caption">HOSPITALITY ARCHITECTURE</div></div>
        </div>
        <div className="side-section-caption">WORKSPACE</div>
        <nav aria-label="Main navigation" className="side-nav">
          <button className={tab === "search" ? "nav-link active" : "nav-link"} onClick={() => { setTab("search"); setMobileNav(false); }}>
            <Sparkles size={19}/> Knowledge Search <ArrowRight className="nav-arrow" size={16}/>
          </button>
          <button className={tab === "library" ? "nav-link active" : "nav-link"} onClick={() => { setTab("library"); setMobileNav(false); }}>
            <FileStack size={19}/> Document Library <ArrowRight className="nav-arrow" size={16}/>
          </button>
        </nav>
        <div className="sidebar-spacer"/>
        <div className="side-divider" />
        <div className="sidebar-footnote">
          <div className="sidebar-footnote-icon"><ShieldCheck size={18}/></div>
          <div><strong>Evidence-first answers</strong><span>Document access is checked before retrieval.</span></div>
        </div>
        <div className="sidebar-identity"><span className="identity-led"/> FICTIONAL COMPANY · LOCAL DEMO</div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="breadcrumb">
            <button className="mobile-menu" onClick={() => setMobileNav((v) => !v)} aria-label="Toggle navigation"><LayoutDashboard size={20}/></button>
            <span className="breadcrumb-home">Studio workspace</span><span className="breadcrumb-slash">/</span>
            <strong>{tab === "search" ? "Knowledge Search" : "Document Library"}</strong>
          </div>
          <div className="account-switcher">
            <span className="account-label">VIEW AS</span>
            <div className="select-wrap">
              <div className="account-avatar">{selected.label.charAt(0)}</div>
              <select aria-label="Select fictional demo identity" value={user} onChange={(e) => setUser(e.target.value as DemoUser)}>
                {USERS.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
              </select>
              <ChevronDown size={16} className="select-arrow"/>
            </div>
          </div>
        </header>


        <main className="page-main">
          {tab === "search" ? (
            <KnowledgeSearch
              key={user}
              user={user}
              onOpenLibrary={() => setTab("library")}
            />
          ) : (
            <DocumentLibrary
              key={user}
              user={user}
            />
          )}
        </main>

        <footer className="footer"><span>ASTERIA STUDIO · KNOWLEDGE INTELLIGENCE</span><span>GROQ · HYBRID RAG · VERIFIED SOURCE EXCERPTS</span></footer>
      </div>
    </div>
  );
}
