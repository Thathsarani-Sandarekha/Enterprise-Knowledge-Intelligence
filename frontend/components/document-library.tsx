"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle, Check, FilePlus2, FileSpreadsheet, FileText, FolderOpen,
  LoaderCircle, LockKeyhole, RefreshCw, UploadCloud,
} from "lucide-react";
import { request } from "@/lib/api";
import type { DemoUser, Document } from "@/lib/api";

const ROLES = [
  { id: "designer", label: "Designers" },
  { id: "procurement", label: "Procurement" },
  { id: "project_manager", label: "Project managers" },
];

function fileIcon(filename: string) {
  return filename.toLowerCase().endsWith(".xlsx") ? <FileSpreadsheet size={21}/> : <FileText size={21}/>;
}

export function DocumentLibrary({ user }: { user: DemoUser }) {
  const admin = user.endsWith("admin");
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [project, setProject] = useState("");
  const [roles, setRoles] = useState<string[]>(["designer", "procurement", "project_manager"]);
  const [editing, setEditing] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [editRoles, setEditRoles] = useState<string[]>([]);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await request<Document[]>("documents", user);
      setDocs(data);
      if (!silent) setError(null);
    } catch (err) { if (!silent) setError(err instanceof Error ? err.message : "Could not load documents"); }
    finally { if (!silent) setLoading(false); }
  }, [user]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!docs.some((doc) => ["queued", "processing"].includes(doc.status))) return;
    const interval = setInterval(() => void load(true), 4_000);
    return () => clearInterval(interval);
  }, [docs, load]);

  const ready = docs.filter((doc) => doc.status === "ready").length;
  const pending = docs.filter((doc) => ["queued", "processing"].includes(doc.status)).length;

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !admin || !roles.length) return;
    setUploading(true); setError(null); setSuccess(null);
    try {
      if (!/\.(pdf|docx|xlsx)$/i.test(file.name)) throw new Error("Only .pdf, .docx, and .xlsx files are supported");
      if (file.size > 15 * 1024 * 1024) throw new Error("Maximum file size is 15 MB");
      const form = new FormData();
      form.set("file", file);
      form.set("allowed_roles", roles.join(","));
      const query = project.trim() ? `?project_code=${encodeURIComponent(project.trim())}` : "";
      await request(`documents${query}`, user, { method: "POST", body: form });
      setFile(null); setSuccess(`“${file.name}” uploaded. Worker will extract and index it.`);
      const picker = document.getElementById("document-picker") as HTMLInputElement | null;
      if (picker) picker.value = "";
      await load(true);
    } catch (err) { setError(err instanceof Error ? err.message : "Upload failed"); }
    finally { setUploading(false); }
  }

  async function savePermissions(documentId: string) {
    if (!admin || !editRoles.length) return;
    setSavingId(documentId); setError(null);
    try {
      await request(`documents/${documentId}/permissions`, user, { method: "PUT", body: JSON.stringify({ allowed_roles: editRoles }) });
      setEditing(null); setSuccess("Permissions saved. Switch identities to verify visibility.");
    } catch (err) { setError(err instanceof Error ? err.message : "Permission change failed"); }
    finally { setSavingId(null); }
  }

  return (
    <div className="content-width">
      <section className="page-intro compact-intro">
        <div className="eyebrow"><span className="eyebrow-line"/> CENTRAL PROJECT KNOWLEDGE</div>
        <h1>Document <em>library.</em></h1>
        <p>Manage hospitality specifications, material approvals, vendor quotations and supporting project records in one searchable place.</p>
      </section>
      <div className="stat-grid">
        <div className="stat-tile"><span>VISIBLE DOCUMENTS</span><strong>{docs.length}</strong><small>Authorized for this demo identity</small></div>
        <div className="stat-tile"><span>READY TO SEARCH</span><strong>{ready}</strong><small>Indexed project sources</small></div>
        <div className="stat-tile"><span>PROCESSING</span><strong>{pending}</strong><small>Ingestion queue</small></div>
      </div>
      {error && <div className="feedback-error" role="alert"><AlertCircle size={17}/>{error}</div>}
      {success && <div className="feedback-success" role="status"><Check size={17}/>{success}</div>}

      {admin && <section className="upload-panel">
        <div className="panel-title-row"><div><span className="section-overline">DOCUMENT INGESTION</span><h2>Add a project record</h2></div><FilePlus2 size={22}/></div>
        <form onSubmit={upload}>
          <label className="file-drop" htmlFor="document-picker">
            <UploadCloud size={27}/><strong>{file ? file.name : "Select a PDF, Word document or Excel workbook"}</strong>
            <span>Maximum 15 MB · Synthetic demo records only</span>
            <input id="document-picker" type="file" accept=".pdf,.docx,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)}/>
          </label>
          <div className="upload-options">
            <label className="field-caption">PROJECT CODE (OPTIONAL)
              <input value={project} onChange={(e) => setProject(e.target.value)} maxLength={80} placeholder="e.g. SGR-2025"/>
            </label>
            <div className="roles-group"><span className="field-caption">ALLOWED DOCUMENT ROLES</span><div className="role-checks">
              {ROLES.map((role) => <label key={role.id}><input type="checkbox" checked={roles.includes(role.id)} onChange={(e) => setRoles((old) => e.target.checked ? [...old, role.id] : old.filter((v) => v !== role.id))}/>{role.label}</label>)}
            </div></div>
          </div>
          <div className="upload-actions"><span><LockKeyhole size={15}/> Only demo admins can upload and grant roles</span>
            <button type="submit" className="primary-button" disabled={!file || !roles.length || uploading}>{uploading ? <><LoaderCircle size={16} className="spin"/> Uploading…</> : <><UploadCloud size={16}/> Upload document</>}</button>
          </div>
        </form>
      </section>}
      {!admin && <div className="access-note"><LockKeyhole size={18}/><div><strong>Read-only document view</strong><span>Use the Studio administrator identity to upload project records or edit grants. This is only a local role simulation.</span></div></div>}

      <section className="library-list-panel">
        <div className="panel-title-row"><div><span className="section-overline">ACCESSIBLE PROJECT RECORDS</span><h2>Documents <span className="count-subtle">{docs.length}</span></h2></div>
          <button className="secondary-button" type="button" onClick={() => void load()} disabled={loading}><RefreshCw size={16} className={loading ? "spin" : ""}/> Refresh</button></div>
        {loading ? <div className="empty-docs"><LoaderCircle className="spin" size={25}/> Loading documents…</div> : docs.length === 0 ? <div className="empty-docs"><FolderOpen size={30}/><strong>No documents visible</strong><span>Switch to Studio administrator to upload sample documents, or change to an authorized demo role.</span></div> :
          <div className="doc-list">{docs.map((doc) => <div className="document-row" key={doc.id}>
            <div className="doc-icon">{fileIcon(doc.filename)}</div>
            <div className="doc-info"><strong title={doc.filename}>{doc.filename}</strong><span>{doc.project_code || "Cross-project reference"} · {doc.chunk_count} chunks · {new Date(doc.created_at).toLocaleDateString()}</span>{doc.error_code && <small className="doc-error">Processing error: {doc.error_code}</small>}</div>
            <span className={`doc-status doc-${doc.status}`}>{doc.status}</span>
            {admin && <button className="permissions-button" onClick={() => { setEditing(editing === doc.id ? null : doc.id); setEditRoles([...ROLES.map((r) => r.id)]); }}><LockKeyhole size={15}/> Access</button>}
            {editing === doc.id && <div className="edit-access"><div className="edit-title">Set allowed roles <small>(current grants are not returned by Task 4)</small></div><div className="role-checks">
              {ROLES.map((role) => <label key={role.id}><input type="checkbox" checked={editRoles.includes(role.id)} onChange={(e) => setEditRoles((old) => e.target.checked ? [...old, role.id] : old.filter((v) => v !== role.id))}/>{role.label}</label>)}
            </div><button className="primary-button small" type="button" disabled={!editRoles.length || savingId === doc.id} onClick={() => void savePermissions(doc.id)}>{savingId === doc.id ? "Saving…" : "Save permissions"}</button></div>}
          </div>)}</div>}
      </section>
      <p className="doc-footer-note">Source-page previews and production authorization are not part of this UI release. Source metadata and verified evidence excerpts are available in Knowledge Search.</p>
    </div>
  );
}
