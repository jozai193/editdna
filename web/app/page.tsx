'use client';
import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AudioLines,
  Scissors,
  FolderOpen,
  Dna,
  FlaskConical,
  Download,
  Upload,
  ArrowRight,
  Check,
  X,
  RotateCcw,
  Play,
  Plus,
  CircleHelp,
  LoaderCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import type {
  State,
  Asset,
  Segment,
  Decision,
  Match,
  Evidence,
  Evaluation,
  EvaluationResult,
  MutationResult,
} from '@/lib/contracts';
const empty: State = {
  assets: [],
  profiles: [],
  pairs: [],
  versions: [],
  plans: [],
  exports: [],
  jobs: [],
};
const time = (s: number) =>
  `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, '0')}`;
function Choice({
  value,
  onChange,
  items,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  items: { id: string; name: string }[];
  label: string;
}) {
  return (
    <Select
      value={value || null}
      onValueChange={(v) => onChange(String(v || ''))}
    >
      <SelectTrigger aria-label={label} className="choice">
        <SelectValue placeholder={label}>
          {items.find((i) => i.id === value)?.name || label}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {items.map((i) => (
          <SelectItem key={i.id} value={i.id}>
            {i.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
function Wave({
  asset,
  segments,
  onSeek,
}: {
  asset: Asset;
  segments?: Segment[];
  onSeek: (t: number) => void;
}) {
  return (
    <div className="wave">
      <div className="wavebars">
        {asset.peaks.map((p: number, i: number) => (
          <span
            key={i}
            style={{
              height: `${Math.max(3, p * 95)}%`,
              opacity:
                segments &&
                !segments.some(
                  (s) =>
                    s.start <= (i / asset.peaks.length) * asset.duration &&
                    s.end >= (i / asset.peaks.length) * asset.duration,
                )
                  ? 0.18
                  : 1,
            }}
          />
        ))}
      </div>
      <input
        aria-label="Seek source recording"
        type="range"
        min="0"
        max={asset.duration}
        step=".1"
        defaultValue="0"
        onChange={(e) => onSeek(Number(e.target.value))}
      />
    </div>
  );
}
export default function Home() {
  const [data, setData] = useState<State>(empty),
    [local, setLocal] = useState(false),
    [loaded, setLoaded] = useState(false),
    [page, setPage] = useState('studio'),
    [busy, setBusy] = useState(''),
    [error, setError] = useState(''),
    [note, setNote] = useState('');
  const [assetId, setAssetId] = useState(''),
    [versionId, setVersionId] = useState(''),
    [planId, setPlanId] = useState(''),
    [pairId, setPairId] = useState(''),
    [profileId, setProfileId] = useState(''),
    [newName, setNewName] = useState(''),
    [rawId, setRawId] = useState(''),
    [finalId, setFinalId] = useState(''),
    [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const sourceVideo = useRef<HTMLVideoElement>(null),
    rawVideo = useRef<HTMLVideoElement>(null),
    finalVideo = useRef<HTMLVideoElement>(null);
  const base = 'http://127.0.0.1:8765/api/v1';
  const asset = data.assets.find((a) => a.id === assetId),
    plan = data.plans.find((p) => p.id === planId),
    pair = data.pairs.find((p) => p.id === pairId),
    version = data.versions.find((v) => v.id === versionId);
  const mediaUrl = (id: string) =>
    local ? `${base}/assets/${id}/media` : `/demo/media/${id}.mp4`;
  const captionUrl = (id: string) =>
    local ? `${base}/assets/${id}/captions.vtt` : `/demo/media/${id}.vtt`;
  const exportUrl = (id: string, file: string) =>
    local ? `${base}/exports/${id}/${file}` : `/demo/exports/${id}/${file}`;
  const profileName = (id: string) =>
    data.profiles.find((p) => p.id === id)?.name || 'Creator';
  const refresh = useCallback(async () => {
    const r = await fetch(local ? `${base}/state` : '/demo/state.json');
    if (!r.ok) throw new Error('Could not load the workspace.');
    const d = (await r.json()) as State;
    setData(d);
    return d as State;
  }, [local]);
  useEffect(() => {
    let active = true;
    async function init() {
      try {
        const isLocal = ['localhost', '127.0.0.1'].includes(
          window.location.hostname,
        );
        const r = await fetch(isLocal ? `${base}/state` : '/demo/state.json');
        if (!r.ok)
          throw new Error(
            isLocal
              ? 'Start the engine with Start-EditDNA.ps1.'
              : 'The demonstration is unavailable.',
          );
        const d: State = await r.json();
        if (!active) return;
        setLocal(isLocal);
        setData(d);
        const a =
          d.assets.find((a) => a.name.includes('accessible')) ||
          d.assets.find((a) => a.role === 'raw');
        setAssetId(a?.id || '');
        const initialPlan = d.plans.find(
          (p) => p.asset_id === a?.id && p.mode === 'personalized',
        );
        setVersionId(
          initialPlan?.profile_version_id || d.versions[0]?.id || '',
        );
        setProfileId(d.profiles[0]?.id || '');
        setPairId(d.pairs[0]?.id || '');
        setPlanId(initialPlan?.id || '');
        const ev = await fetch(
          isLocal ? `${base}/evaluation` : '/demo/evaluation.json',
        );
        if (ev.ok && active) setEvaluation(await ev.json());
      } catch (e) {
        if (active) setError(String(e));
      } finally {
        if (active) setLoaded(true);
      }
    }
    void init();
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    if (!local) return;
    const id = setInterval(() => {
      refresh().catch(() => {});
    }, 2500);
    return () => clearInterval(id);
  }, [local, refresh]);
  async function action(
    label: string,
    path: string,
    body?: unknown,
    method: 'POST' | 'PATCH' = 'POST',
    revision?: number,
  ) {
    setBusy(label);
    setError('');
    setNote('');
    try {
      if (!local)
        throw new Error('Open the local app to process your own recordings.');
      const r = await fetch(`${base}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(revision ? { 'If-Match': String(revision) } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      const result = (await r.json()) as MutationResult;
      if (!r.ok)
        throw new Error(
          typeof result.detail === 'string'
            ? result.detail
            : 'Check your inputs and try again.',
        );
      await refresh();
      setNote(
        result.status === 'queued'
          ? `${label} queued for processing.`
          : `${label} complete.`,
      );
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy('');
    }
  }
  async function upload(file: File) {
    setBusy('Importing recording');
    setError('');
    try {
      const f = new FormData();
      f.append('file', file);
      const r = await fetch(`${base}/assets`, { method: 'POST', body: f });
      const a = (await r.json()) as Asset & { detail?: string };
      if (!r.ok) throw new Error(a.detail || 'Import failed');
      await refresh();
      setAssetId(a.id);
      setNote('Recording imported.');
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy('');
    }
  }
  async function generate(mode: string) {
    if (!assetId) return;
    if (!local) {
      const p = data.plans.find(
        (p) =>
          p.asset_id === assetId &&
          (mode === 'generic'
            ? p.mode === 'generic'
            : p.profile_version_id === versionId),
      );
      if (p) setPlanId(p.id);
      else
        setError(
          'No recorded edit exists for this combination. Use the local app to create it.',
        );
      return;
    }
    const p = await action('Create edit', '/plans', {
      asset_id: assetId,
      profile_version_id: mode === 'generic' ? null : versionId,
    });
    if (p) setPlanId(p.id);
  }
  async function changeSegments(segments: Segment[]) {
    if (plan)
      await action(
        'Save revision',
        `/plans/${plan.id}`,
        { segments },
        'PATCH',
        plan.revision,
      );
  }
  const activeJobs = data.jobs.filter((j) =>
    ['queued', 'running'].includes(j.status),
  );
  const appliedVersion = plan?.profile_version_id
    ? data.versions.find((v) => v.id === plan.profile_version_id)
    : version;
  const currentExport = plan
    ? data.exports.find(
        (e) => e.plan_id === plan.id && e.revision === plan.revision,
      )
    : null;
  const nav = [
    { id: 'studio', name: 'Edit workspace', icon: Scissors },
    { id: 'library', name: 'Example library', icon: FolderOpen },
    { id: 'profile', name: 'Creator profiles', icon: Dna },
    { id: 'evaluation', name: 'Evidence & exports', icon: FlaskConical },
  ];
  return (
    <SidebarProvider>
      <Sidebar className="studio-sidebar">
        <SidebarHeader>
          <Link className="brand" href="/">
            <AudioLines size={30} />
            <span>
              Edit<span className="mint">DNA</span>
            </span>
          </Link>
          <div className="workspace-label">PERSONAL EDITING STUDIO</div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarMenu>
            {nav.map((n) => (
              <SidebarMenuItem key={n.id}>
                <SidebarMenuButton
                  isActive={page === n.id}
                  onClick={() => setPage(n.id)}
                  className="nav-item"
                >
                  <n.icon size={19} />
                  <span>{n.name}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
          <div className="sidebar-note">
            <Dna size={22} />
            <strong>Your edits are the instructions.</strong>
            <p>Learn a preference. See the evidence. Keep the final say.</p>
          </div>
        </SidebarContent>
        <SidebarFooter>
          {local && <Link href="/trial">Timed editing trial →</Link>}
          <span className="engine-status">
            <i />
            {local ? 'Local engine connected' : 'Recorded demonstration'}
          </span>
          <small>Original media stays on your device in the local app.</small>
        </SidebarFooter>
      </Sidebar>
      <main className="main-surface">
        <header className="topbar">
          <div className="breadcrumb">
            <SidebarTrigger />
            <span>Studio</span>
            <span>/</span>
            <strong>{nav.find((n) => n.id === page)?.name}</strong>
          </div>
          <span className="pill">
            {local ? 'LOCAL · v0.1' : 'DEMO · OWNED FOOTAGE'}
          </span>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                {page === 'studio'
                  ? 'FROM EXAMPLES TO YOUR NEXT EDIT'
                  : 'YOUR EDITING MEMORY'}
              </p>
              <h1>
                {page === 'studio'
                  ? 'Make the next cut yours.'
                  : page === 'library'
                    ? 'Show it how you edit.'
                    : page === 'profile'
                      ? 'A style you can inspect.'
                      : 'Proof, before promises.'}
              </h1>
            </div>
            {local && (
              <label className="import-button">
                <Upload size={17} /> Import recording
                <input
                  type="file"
                  accept="video/*,audio/*"
                  disabled={!!busy}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void upload(f);
                    e.target.value = '';
                  }}
                />
              </label>
            )}
          </div>
          {!local && loaded && (
            <div className="demo-banner">
              <CircleHelp size={18} />
              <span>
                Actual outputs from five original, synthesized tutorials.
                Preferences are constructed for this demonstration; creator
                outcomes have not been validated.
              </span>
              <Link
                className="download-button"
                href="/downloads/editdna-source.zip"
                download
              >
                <Download size={15} /> Get local app
              </Link>
              <Link href="/downloads/editdna-demo.mp4">Watch walkthrough</Link>
            </div>
          )}
          {error && (
            <div role="alert" className="notice error">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError('')}>
                <X size={18} />
              </button>
            </div>
          )}
          {note && <output className="notice">{note}</output>}
          {(busy || activeJobs.length > 0) && (
            <output className="jobbar">
              <LoaderCircle className="spin" size={18} />
              {busy || `${activeJobs[0].task} · ${activeJobs[0].status}`}
              <span>Processing continues in the background.</span>
            </output>
          )}
          {!loaded ? (
            <div className="empty-state">Loading your workspace…</div>
          ) : (
            <>
              {page === 'studio' && (
                <>
                  <div className="toolbar">
                    <div className="field-label">
                      RECORDING
                      <Choice
                        label="Choose raw footage"
                        value={assetId}
                        onChange={(v) => {
                          setAssetId(v);
                          setPlanId('');
                        }}
                        items={data.assets.filter((a) => a.role === 'raw')}
                      />
                    </div>
                    <div className="field-label">
                      EDITING PROFILE
                      <Choice
                        label="Choose a learned profile"
                        value={versionId}
                        onChange={setVersionId}
                        items={data.versions.map((v) => ({
                          id: v.id,
                          name: `${profileName(v.profile_id)} · v${v.number}`,
                        }))}
                      />
                    </div>
                    <Button
                      className="primary-action"
                      disabled={!assetId || !versionId || !!busy}
                      onClick={() => generate('personalized')}
                    >
                      <Scissors />{' '}
                      {local ? 'Create my edit' : 'View example edit'}
                    </Button>
                  </div>
                  {asset ? (
                    <div className="editor-grid">
                      <section className="panel editor-panel">
                        <div className="panel-heading">
                          <span>
                            <span className="status-dot" />{' '}
                            {plan ? 'Review your edit' : 'Source preview'}
                          </span>
                          <span className="mono">
                            {time(plan?.duration || asset.duration)}
                          </span>
                        </div>
                        <Tabs defaultValue="source">
                          <TabsList className="preview-tabs">
                            <TabsTrigger value="source">
                              Original recording
                            </TabsTrigger>
                            <TabsTrigger value="render">
                              Rendered edit{' '}
                              {currentExport && <Check size={14} />}
                            </TabsTrigger>
                          </TabsList>
                          <TabsContent value="source">
                            <video
                              key={asset.id}
                              ref={sourceVideo}
                              controls
                              preload="metadata"
                              crossOrigin="anonymous"
                              src={mediaUrl(asset.id)}
                              className="preview-video"
                            >
                              <track
                                kind="captions"
                                srcLang="en"
                                label="English"
                                src={captionUrl(asset.id)}
                              />
                            </video>
                          </TabsContent>
                          <TabsContent value="render">
                            {currentExport ? (
                              <video
                                key={currentExport.id}
                                controls
                                crossOrigin="anonymous"
                                src={exportUrl(currentExport.id, 'edit.mp4')}
                                className="preview-video"
                              >
                                <track
                                  kind="captions"
                                  srcLang="en"
                                  label="English"
                                  src={exportUrl(
                                    currentExport.id,
                                    'captions.vtt',
                                  )}
                                />
                              </video>
                            ) : (
                              <div className="render-empty">
                                <Scissors size={32} />
                                <h3>Render the reviewed plan</h3>
                                <p>
                                  The preview will contain the exact cuts in
                                  your export.
                                </p>
                                <Button
                                  disabled={!local || !plan || !!busy}
                                  onClick={() =>
                                    plan &&
                                    action(
                                      'Render edit',
                                      `/plans/${plan.id}/export`,
                                    )
                                  }
                                >
                                  Render MP4
                                </Button>
                              </div>
                            )}
                          </TabsContent>
                        </Tabs>
                        <div className="timeline">
                          <div className="timeline-label">
                            <span>SOURCE AUDIO</span>
                            <span>Dimmed sections are removed</span>
                          </div>
                          <Wave
                            asset={asset}
                            segments={plan?.segments}
                            onSeek={(t) => {
                              if (sourceVideo.current)
                                sourceVideo.current.currentTime = t;
                            }}
                          />
                          <div className="ruler">
                            <span>0:00</span>
                            <span>{time(asset.duration / 2)}</span>
                            <span>{time(asset.duration)}</span>
                          </div>
                        </div>
                        <div className="editor-actions">
                          <Button
                            variant="outline"
                            disabled={!!busy}
                            onClick={() => generate('generic')}
                          >
                            Compare generic edit
                          </Button>
                          <Button
                            variant="outline"
                            disabled={!local || !plan?.history.length || !!busy}
                            onClick={() =>
                              plan &&
                              action(
                                'Undo edit',
                                `/plans/${plan.id}/undo`,
                                undefined,
                                'POST',
                                plan.revision,
                              )
                            }
                          >
                            <RotateCcw /> Undo
                          </Button>
                          {currentExport ? (
                            <a
                              className="download-button"
                              href={exportUrl(
                                currentExport.id,
                                'editdna-export.zip',
                              )}
                            >
                              <Download size={16} /> Download export
                            </a>
                          ) : (
                            <Button
                              disabled={!local || !plan || !!busy}
                              onClick={() =>
                                plan &&
                                action(
                                  'Render edit',
                                  `/plans/${plan.id}/export`,
                                )
                              }
                            >
                              <Download /> Render & export
                            </Button>
                          )}
                        </div>
                      </section>
                      <aside className="evidence-panel">
                        <div className="eyebrow">APPLIED PREFERENCE</div>
                        <Dna className="large-icon" />
                        <h2>
                          {plan?.mode === 'generic'
                            ? 'Generic baseline'
                            : appliedVersion
                              ? profileName(appliedVersion.profile_id)
                              : 'Choose a profile'}
                        </h2>
                        <p>
                          {plan?.mode === 'generic'
                            ? 'A fixed 0.35 second pause target.'
                            : appliedVersion
                              ? `Learned from ${appliedVersion.session_count} source sessions and ${appliedVersion.observation_count} observed pauses.`
                              : 'Learn from examples to personalize your next edit.'}
                        </p>
                        <div className="big-metric">
                          {(plan?.mode === 'generic'
                            ? 0.35
                            : appliedVersion?.pause_seconds || 0
                          ).toFixed(2)}
                          <span>seconds</span>
                        </div>
                        <span className="metric-label">
                          target pause between phrases
                        </span>
                        <div className="take-preference">
                          <strong>
                            {plan?.take_preference
                              ? `Keep the ${plan.take_preference} equivalent take`
                              : 'Keep every take'}
                          </strong>
                          <small>
                            {plan?.take_preference
                              ? 'Supported by accepted example edits'
                              : 'No take preference applied'}
                          </small>
                        </div>
                        <div className="evidence-divider" />
                        <div className="fact">
                          <Check size={16} />
                          <span>Speech and source order preserved</span>
                        </div>
                        <div className="fact">
                          <Check size={16} />
                          <span>Every cut remains editable</span>
                        </div>
                        <div className="fact muted">
                          <CircleHelp size={16} />
                          <span>
                            {plan?.visual?.origin === 'learned'
                              ? `Learned centered framing: ${plan.visual.zoom.toFixed(2)}× from ${plan.visual.session_count} sessions`
                              : 'Centered framing: default or manually set'}
                          </span>
                        </div>
                        {plan && (
                          <label htmlFor="framing-zoom">
                            Centered framing
                            <Input
                              id="framing-zoom"
                              key={`${plan.id}-${plan.revision}`}
                              aria-label="Centered framing zoom"
                              type="number"
                              min="1"
                              max="1.4"
                              step="0.01"
                              defaultValue={plan.visual?.zoom || 1}
                              disabled={!local || !!busy}
                              onBlur={(e) => {
                                const zoom = Number(e.target.value);
                                if (
                                  zoom >= 1 &&
                                  zoom <= 1.4 &&
                                  zoom !== (plan.visual?.zoom || 1)
                                )
                                  void action(
                                    'Set framing',
                                    `/plans/${plan.id}`,
                                    {
                                      segments: plan.segments,
                                      visual: { zoom },
                                    },
                                    'PATCH',
                                    plan.revision,
                                  );
                              }}
                            />
                            <small>
                              Applied during render. Check faces and edge text.
                              Graphics, grading, and crop timing are not
                              learned.
                            </small>
                          </label>
                        )}
                        <Button
                          variant="ghost"
                          onClick={() => setPage('profile')}
                        >
                          Inspect the evidence <ArrowRight />
                        </Button>
                      </aside>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <Upload size={34} />
                      <h2>Bring your next recording.</h2>
                      <p>
                        Import a video or audio file with a clear spoken track.
                      </p>
                    </div>
                  )}
                  {plan && asset && (
                    <section className="panel decisions-panel">
                      <div className="panel-heading">
                        <h2>
                          Cut decisions{' '}
                          <span className="count">{plan.decisions.length}</span>
                        </h2>
                        <span className="mono">
                          {(asset.duration - plan.duration).toFixed(1)}s removed
                          · revision {plan.revision}
                        </span>
                      </div>
                      <p className="section-note">
                        {plan.mode === 'generic'
                          ? 'Generic baseline'
                          : 'Personalized pause edit'}{' '}
                        · Adjust source boundaries or restore a pause before
                        rendering.
                      </p>
                      <div className="take-review">
                        {plan.decisions
                          .filter((d: Decision) => d.kind === 'take')
                          .map((d: Decision) => (
                            <div key={d.id}>
                              <Scissors size={15} />
                              <span>
                                {d.reason} Removed {time(d.start)}–{time(d.end)}
                                .
                              </span>
                              <Button
                                variant="outline"
                                disabled={
                                  !local ||
                                  !!busy ||
                                  plan.segments.some(
                                    (s: Segment) =>
                                      s.start <= d.start + 0.02 &&
                                      s.end >= d.end - 0.02,
                                  )
                                }
                                onClick={() =>
                                  changeSegments(
                                    [
                                      ...plan.segments,
                                      {
                                        id: `restored-${d.id}`,
                                        start: d.start,
                                        end: d.end,
                                        text: 'Restored take',
                                      },
                                    ].sort(
                                      (a: Segment, b: Segment) =>
                                        a.start - b.start,
                                    ),
                                  )
                                }
                              >
                                Restore take
                              </Button>
                            </div>
                          ))}
                      </div>
                      <div className="segment-list">
                        {plan.segments.map((s: Segment, i: number) => (
                          <div
                            className="segment-row"
                            key={`${plan.id}-${plan.revision}-${s.id}`}
                          >
                            <button
                              className="segment-play"
                              aria-label={`Play segment ${i + 1}`}
                              onClick={() => {
                                if (sourceVideo.current) {
                                  sourceVideo.current.currentTime = s.start;
                                  void sourceVideo.current
                                    .play()
                                    .catch(() => {});
                                }
                              }}
                            >
                              <Play size={15} />
                            </button>
                            <span className="mono segment-index">
                              {String(i + 1).padStart(2, '0')}
                            </span>
                            <div className="segment-copy">
                              <strong>
                                {s.text || `Speech segment ${i + 1}`}
                              </strong>
                              <small>
                                {plan.decisions.find(
                                  (d: Decision) =>
                                    d.id === s.id.replace('s', 'd'),
                                )?.reason || 'Keep the spoken content.'}
                              </small>
                            </div>
                            <label>
                              IN
                              <input
                                aria-label={`Segment ${i + 1} start`}
                                type="number"
                                step="0.01"
                                defaultValue={s.start.toFixed(2)}
                                disabled={!local || !!busy || s.locked}
                                onBlur={(e) => {
                                  const n = Number(e.target.value);
                                  if (Math.abs(n - s.start) > 0.006)
                                    void changeSegments(
                                      plan.segments.map((x: Segment) =>
                                        x.id === s.id ? { ...x, start: n } : x,
                                      ),
                                    );
                                }}
                              />
                            </label>
                            <label>
                              OUT
                              <input
                                aria-label={`Segment ${i + 1} end`}
                                type="number"
                                step="0.01"
                                defaultValue={s.end.toFixed(2)}
                                disabled={!local || !!busy || s.locked}
                                onBlur={(e) => {
                                  const n = Number(e.target.value);
                                  if (Math.abs(n - s.end) > 0.006)
                                    void changeSegments(
                                      plan.segments.map((x: Segment) =>
                                        x.id === s.id ? { ...x, end: n } : x,
                                      ),
                                    );
                                }}
                              />
                            </label>
                            {i < plan.segments.length - 1 && (
                              <Button
                                variant="ghost"
                                disabled={!local || !!busy || s.locked}
                                onClick={() =>
                                  changeSegments(
                                    plan.segments.map((x: Segment) =>
                                      x.id === s.id
                                        ? {
                                            ...x,
                                            end: plan.segments[i + 1].start,
                                          }
                                        : x,
                                    ),
                                  )
                                }
                              >
                                {plan.decisions.some(
                                  (d: Decision) =>
                                    d.kind === 'take' &&
                                    d.start >= s.end &&
                                    d.end <= plan.segments[i + 1].start,
                                )
                                  ? 'Restore gap & take'
                                  : 'Restore pause'}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              disabled={!local || !!busy}
                              onClick={() =>
                                changeSegments(
                                  plan.segments.map((x) =>
                                    x.id === s.id
                                      ? { ...x, locked: !x.locked }
                                      : x,
                                  ),
                                )
                              }
                            >
                              {s.locked ? 'Unlock' : 'Lock'}
                            </Button>
                            <Button
                              variant="ghost"
                              disabled={
                                !local ||
                                !!busy ||
                                s.locked ||
                                plan.segments.length === 1
                              }
                              onClick={() =>
                                changeSegments(
                                  plan.segments.filter((x) => x.id !== s.id),
                                )
                              }
                            >
                              Remove
                            </Button>
                          </div>
                        ))}
                      </div>
                      {local && asset.words.length === 0 && (
                        <div className="section-note">
                          Transcript not generated.{' '}
                          <Button
                            variant="outline"
                            disabled={!!busy}
                            onClick={() =>
                              action(
                                'Transcribe recording',
                                `/assets/${asset.id}/transcribe`,
                              )
                            }
                          >
                            Transcribe locally
                          </Button>{' '}
                          First use downloads the speech model.
                        </div>
                      )}
                    </section>
                  )}
                </>
              )}
              {page === 'library' && (
                <>
                  <div className="two-column">
                    <section className="panel">
                      <div className="panel-heading">
                        <h2>Example pairs</h2>
                        <span className="count">{data.pairs.length}</span>
                      </div>
                      {data.pairs.map((p) => (
                        <button
                          key={p.id}
                          className={`pair-item ${p.id === pairId ? 'selected' : ''}`}
                          onClick={() => setPairId(p.id)}
                        >
                          <span className="pair-icon">
                            <AudioLines />
                          </span>
                          <span>
                            <strong>{p.name}</strong>
                            <small>
                              {profileName(p.profile_id)} ·{' '}
                              {p.alignment
                                ? `${p.alignment.matches.filter((m: Match) => m.status === 'accepted').length} accepted matches`
                                : 'Ready to analyze'}
                            </small>
                          </span>
                          <ArrowRight size={17} />
                        </button>
                      ))}
                    </section>
                    <section className="panel form-panel">
                      <h2>Add an example</h2>
                      <p>
                        Pair an original recording with the edit you made from
                        it.
                      </p>
                      <Choice
                        label="Creator profile"
                        value={profileId}
                        onChange={setProfileId}
                        items={data.profiles}
                      />
                      <Choice
                        label="Raw recording"
                        value={rawId}
                        onChange={setRawId}
                        items={data.assets}
                      />
                      <Choice
                        label="Finished edit"
                        value={finalId}
                        onChange={setFinalId}
                        items={data.assets}
                      />
                      <Button
                        disabled={
                          !local || !rawId || !finalId || !profileId || !!busy
                        }
                        onClick={async () => {
                          const p = await action('Add pair', '/pairs', {
                            profile_id: profileId,
                            raw_id: rawId,
                            final_id: finalId,
                            name:
                              data.assets.find((a) => a.id === rawId)?.name ||
                              'New example',
                          });
                          if (p) setPairId(p.id);
                        }}
                      >
                        <Plus /> Add pair
                      </Button>
                    </section>
                  </div>
                  {pair && (
                    <section className="panel alignment-panel">
                      <div className="panel-heading">
                        <h2>{pair.name}</h2>
                        <Button
                          variant="outline"
                          disabled={!local || !!busy}
                          onClick={() =>
                            action('Analyze pair', `/pairs/${pair.id}/analyze`)
                          }
                        >
                          Analyze audio alignment
                        </Button>
                      </div>
                      <div className="paired-videos">
                        <div>
                          <p className="eyebrow">RAW SOURCE</p>
                          <video
                            ref={rawVideo}
                            key={pair.raw_id}
                            controls
                            crossOrigin="anonymous"
                            src={mediaUrl(pair.raw_id)}
                          >
                            <track
                              kind="captions"
                              srcLang="en"
                              label="English"
                              src={captionUrl(pair.raw_id)}
                            />
                          </video>
                        </div>
                        <div>
                          <p className="eyebrow">FINISHED EDIT</p>
                          <video
                            ref={finalVideo}
                            key={pair.final_id}
                            controls
                            crossOrigin="anonymous"
                            src={mediaUrl(pair.final_id)}
                          >
                            <track
                              kind="captions"
                              srcLang="en"
                              label="English"
                              src={captionUrl(pair.final_id)}
                            />
                          </video>
                        </div>
                      </div>
                      {pair.alignment ? (
                        <>
                          <div className="scope-note">
                            <h3>Visual evidence · centered framing</h3>
                            <Button
                              disabled={!local || !!busy}
                              onClick={() =>
                                action(
                                  'Analyze framing',
                                  `/pairs/${pair.id}/visual`,
                                )
                              }
                            >
                              Analyze corresponding frames
                            </Button>
                            <p>
                              Review each matched frame pair before accepting.
                              Three independent source sessions are required to
                              learn a fixed crop.
                            </p>
                            {pair.visual?.observations.map((o, i) => (
                              <div key={i} className="evidence-link">
                                <button
                                  onClick={() => {
                                    if (rawVideo.current)
                                      rawVideo.current.currentTime = o.raw_time;
                                    if (finalVideo.current)
                                      finalVideo.current.currentTime =
                                        o.final_time;
                                  }}
                                >
                                  Inspect {time(o.raw_time)} →{' '}
                                  {time(o.final_time)}
                                </button>
                                <span>
                                  {o.zoom
                                    ? `${o.zoom.toFixed(2)}× · ${o.status}`
                                    : o.reason}
                                </span>
                                <Button
                                  disabled={
                                    !local ||
                                    !!busy ||
                                    o.status === 'unresolved' ||
                                    o.status === 'accepted'
                                  }
                                  onClick={() =>
                                    action(
                                      'Accept framing',
                                      `/pairs/${pair.id}/visual`,
                                      {
                                        observations: [
                                          {
                                            match_id: o.match_id,
                                            status: 'accepted',
                                          },
                                        ],
                                      },
                                      'PATCH',
                                      pair.revision,
                                    )
                                  }
                                >
                                  Accept framing
                                </Button>
                                <Button
                                  variant="ghost"
                                  disabled={!local || !!busy}
                                  onClick={() =>
                                    action(
                                      'Reject framing',
                                      `/pairs/${pair.id}/visual`,
                                      {
                                        observations: [
                                          {
                                            match_id: o.match_id,
                                            status: 'rejected',
                                          },
                                        ],
                                      },
                                      'PATCH',
                                      pair.revision,
                                    )
                                  }
                                >
                                  Reject
                                </Button>
                              </div>
                            ))}
                          </div>
                          <div className="panel-heading">
                            <p>
                              {pair.alignment.matches.length} candidate matches
                              · Review before learning.
                            </p>
                            <Button
                              disabled={!local || !!busy}
                              onClick={() =>
                                action(
                                  'Accept strong matches',
                                  `/pairs/${pair.id}/alignment`,
                                  {
                                    matches: (pair.alignment?.matches || [])
                                      .filter(
                                        (m: Match) => m.status === 'proposed',
                                      )
                                      .map((m: Match) => ({
                                        id: m.id,
                                        status: 'accepted',
                                      })),
                                  },
                                  'PATCH',
                                  pair.revision,
                                )
                              }
                            >
                              Accept unambiguous matches
                            </Button>
                          </div>
                          <div className="match-list">
                            {pair.alignment.matches.map((m: Match) => (
                              <div
                                className="match-row"
                                key={`${pair.id}-${pair.revision}-${m.id}`}
                              >
                                <button
                                  className="segment-play"
                                  aria-label="Play corresponding match"
                                  onClick={() => {
                                    if (rawVideo.current) {
                                      rawVideo.current.currentTime =
                                        m.raw_start;
                                      void rawVideo.current
                                        .play()
                                        .catch(() => {});
                                    }
                                    if (finalVideo.current)
                                      finalVideo.current.currentTime =
                                        m.final_start;
                                  }}
                                >
                                  <Play size={15} />
                                </button>
                                <span className="mono">
                                  {time(m.final_start)} → {time(m.raw_start)}
                                </span>
                                <span>Correlation {m.score.toFixed(3)}</span>
                                <span className={`match-status ${m.status}`}>
                                  {m.status}
                                </span>
                                {m.alternatives.length > 1 && (
                                  <div className="match-alternatives">
                                    {m.alternatives.map((a, i) => (
                                      <Button
                                        key={i}
                                        variant="outline"
                                        disabled={!local || !!busy}
                                        onClick={() =>
                                          action(
                                            'Choose source match',
                                            `/pairs/${pair.id}/alignment`,
                                            {
                                              matches: [
                                                {
                                                  id: m.id,
                                                  raw_start: a.start,
                                                  status: 'proposed',
                                                },
                                              ],
                                            },
                                            'PATCH',
                                            pair.revision,
                                          )
                                        }
                                      >
                                        Source {time(a.start)}
                                      </Button>
                                    ))}
                                  </div>
                                )}
                                <input
                                  className="match-time"
                                  aria-label={`Source start for match ${m.id}`}
                                  type="number"
                                  step="0.01"
                                  key={`${pair.revision}-${m.id}`}
                                  defaultValue={m.raw_start.toFixed(2)}
                                  disabled={!local || !!busy}
                                  onBlur={(e) => {
                                    const value = Number(e.target.value);
                                    if (Math.abs(value - m.raw_start) > 0.006)
                                      void action(
                                        'Adjust match',
                                        `/pairs/${pair.id}/alignment`,
                                        {
                                          matches: [
                                            {
                                              id: m.id,
                                              raw_start: value,
                                              status: 'proposed',
                                            },
                                          ],
                                        },
                                        'PATCH',
                                        pair.revision,
                                      );
                                  }}
                                />
                                <Button
                                  variant="ghost"
                                  aria-label="Accept match"
                                  disabled={!local || !!busy}
                                  onClick={() =>
                                    action(
                                      'Accept match',
                                      `/pairs/${pair.id}/alignment`,
                                      {
                                        matches: [
                                          { id: m.id, status: 'accepted' },
                                        ],
                                      },
                                      'PATCH',
                                      pair.revision,
                                    )
                                  }
                                >
                                  <Check />
                                </Button>
                                <Button
                                  variant="ghost"
                                  aria-label="Reject match"
                                  disabled={!local || !!busy}
                                  onClick={() =>
                                    action(
                                      'Reject match',
                                      `/pairs/${pair.id}/alignment`,
                                      {
                                        matches: [
                                          { id: m.id, status: 'rejected' },
                                        ],
                                      },
                                      'PATCH',
                                      pair.revision,
                                    )
                                  }
                                >
                                  <X />
                                </Button>
                              </div>
                            ))}
                          </div>
                        </>
                      ) : (
                        <div className="empty-state">
                          Analyze this pair to locate each finished phrase in
                          the original.
                        </div>
                      )}
                    </section>
                  )}
                </>
              )}
              {page === 'profile' && (
                <>
                  <div className="toolbar">
                    <Choice
                      label="Creator profile"
                      value={profileId}
                      onChange={setProfileId}
                      items={data.profiles}
                    />
                    <Input
                      aria-label="New profile name"
                      placeholder="New profile name"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                    />
                    <Button
                      variant="outline"
                      disabled={!local || !newName.trim() || !!busy}
                      onClick={async () => {
                        const p = await action('Create profile', '/profiles', {
                          name: newName.trim(),
                        });
                        if (p) {
                          setProfileId(p.id);
                          setNewName('');
                        }
                      }}
                    >
                      <Plus /> New profile
                    </Button>
                    <Button
                      disabled={!local || !profileId || !!busy}
                      onClick={async () => {
                        const v = await action(
                          'Learn profile',
                          `/profiles/${profileId}/learn`,
                        );
                        if (v) setVersionId(v.id);
                      }}
                    >
                      <Dna /> Learn from accepted examples
                    </Button>
                  </div>
                  <div className="profile-cards">
                    {data.versions
                      .filter((v) => !profileId || v.profile_id === profileId)
                      .map((v) => (
                        <section className="panel profile-card" key={v.id}>
                          <div className="panel-heading">
                            <h2>{profileName(v.profile_id)}</h2>
                            <span className="pill">VERSION {v.number}</span>
                          </div>
                          <div className="big-metric">
                            {v.pause_seconds.toFixed(2)}
                            <span>seconds</span>
                          </div>
                          <p>Learned pause target · {v.confidence} evidence</p>
                          <div className="stats-row">
                            <div>
                              <strong>{v.session_count}</strong>
                              <span>source sessions</span>
                            </div>
                            <div>
                              <strong>{v.observation_count}</strong>
                              <span>pause observations</span>
                            </div>
                          </div>
                          <div className="scope-note">
                            <strong>
                              {v.take_preference
                                ? `Keep the ${v.take_preference} equivalent take`
                                : 'Take preference unknown'}
                            </strong>
                            <p>
                              {v.take_evidence?.length || 0} observed selections
                              across the training examples. Different numbers
                              and negations are never treated as equivalent.
                            </p>
                          </div>
                          <h3>What informed this preference</h3>
                          <p>
                            {v.visual?.status === 'learned'
                              ? `Centered framing: ${v.visual.zoom?.toFixed(2)}×, supported by ${v.visual.session_count} independent source sessions.`
                              : v.visual?.reason ||
                                'No visual framing evidence yet.'}
                          </p>
                          {v.evidence
                            .slice(0, 6)
                            .map((e: Evidence, i: number) => (
                              <button
                                className="evidence-link"
                                key={i}
                                onClick={() => {
                                  setPairId(e.pair_id);
                                  setPage('library');
                                }}
                              >
                                <span>
                                  {
                                    data.pairs.find((p) => p.id === e.pair_id)
                                      ?.name
                                  }
                                </span>
                                <span className="mono">
                                  {e.raw_pause.toFixed(2)}s →{' '}
                                  {e.kept_pause.toFixed(2)}s
                                </span>
                                <ArrowRight size={15} />
                              </button>
                            ))}
                          <div className="scope-note">
                            <strong>Not enough evidence for</strong>
                            <p>{v.unknown.join(' · ')}</p>
                          </div>
                          <Button
                            variant="outline"
                            onClick={() => {
                              setVersionId(v.id);
                              setPage('studio');
                            }}
                          >
                            Use this version <ArrowRight />
                          </Button>
                        </section>
                      ))}
                  </div>
                  {!data.versions.some((v) => v.profile_id === profileId) && (
                    <div className="empty-state">
                      <Dna size={32} />
                      <h2>No learned version yet.</h2>
                      <p>
                        Accept reliable matches in your example pairs, then
                        learn a profile.
                      </p>
                    </div>
                  )}
                </>
              )}
              {page === 'evaluation' && (
                <>
                  <section className="panel evaluation-panel">
                    <div className="panel-heading">
                      <h2>Held-out evaluation</h2>
                      <span className="pill">MEASURED LOCALLY</span>
                    </div>
                    {evaluation?.status === 'complete' ? (
                      <>
                        <div className="stats-row">
                          <div>
                            <strong>{evaluation.training_sessions}</strong>
                            <span>training sessions</span>
                          </div>
                          <div>
                            <strong>{evaluation.held_out_sessions}</strong>
                            <span>held-out sessions</span>
                          </div>
                          <div>
                            <strong>
                              {evaluation.alignment_precision_pct}%
                            </strong>
                            <span>accepted alignment precision</span>
                          </div>
                          <div>
                            <strong>
                              {evaluation.correspondence_median_ms}ms
                            </strong>
                            <span>median audio correspondence error</span>
                          </div>
                        </div>
                        <p>{evaluation.summary}</p>
                        {evaluation.results?.map(
                          (r: EvaluationResult, i: number) => (
                            <div className="match-row" key={i}>
                              <strong>{r.profile}</strong>
                              <span>
                                Session {r.session} · {r.split}
                              </span>
                              <span>
                                Target error: {r.personalized_error_ms}ms
                              </span>
                              <span>Generic error: {r.generic_error_ms}ms</span>
                              <span>
                                Take agreement: {r.take_agreement_pct}%
                              </span>
                              <span>
                                Framing: {r.framing_zoom?.toFixed(2)}× ·
                                reference error {r.framing_error?.toFixed(3)}
                              </span>
                              <span className="match-status accepted">
                                {r.personalized_error_ms < r.generic_error_ms
                                  ? 'Closer to reference'
                                  : 'No improvement'}
                              </span>
                            </div>
                          ),
                        )}
                        <div className="scope-note">
                          {evaluation.limitations}
                        </div>
                      </>
                    ) : (
                      <p>
                        Evaluation has not run yet. No performance result is
                        claimed.
                      </p>
                    )}
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Rendered exports</h2>
                      <span className="count">{data.exports.length}</span>
                    </div>
                    {data.exports.map((e) => (
                      <div className="export-row" key={e.id}>
                        <span className="pair-icon">
                          <Scissors />
                        </span>
                        <div>
                          <strong>
                            {data.assets.find(
                              (a) =>
                                a.id ===
                                data.plans.find((p) => p.id === e.plan_id)
                                  ?.asset_id,
                            )?.name || 'Edited recording'}
                          </strong>
                          <small>
                            {time(e.duration)} · revision {e.revision} ·{' '}
                            {e.has_captions
                              ? 'captions included'
                              : 'transcript not generated'}
                          </small>
                        </div>
                        <a href={exportUrl(e.id, 'edit.mp4')}>MP4</a>
                        <a href={exportUrl(e.id, 'edit-plan.json')}>
                          Edit plan
                        </a>
                        <a
                          className="download-button"
                          href={exportUrl(e.id, 'editdna-export.zip')}
                        >
                          <Download size={16} /> Export bundle
                        </a>
                      </div>
                    ))}
                  </section>
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>Processing history</h2>
                    </div>
                    {data.jobs.slice(0, 12).map((j) => (
                      <div className="match-row" key={j.id}>
                        <strong>{j.task}</strong>
                        <span
                          className={`match-status ${j.status === 'complete' ? 'accepted' : ''}`}
                        >
                          {j.status}
                        </span>
                        <span className="job-message">{j.message}</span>
                      </div>
                    ))}
                  </section>
                </>
              )}
            </>
          )}
        </div>
        <footer className="app-footer">
          EditDNA · Learn the repeated decisions. Review every cut.
        </footer>
      </main>
    </SidebarProvider>
  );
}
