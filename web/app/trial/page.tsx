'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { Plan, State } from '@/lib/contracts';
const api = 'http://127.0.0.1:8765/api/v1';
type Trial = {
  id: string;
  status: string;
  order: string[];
  active?: {
    plan_id: string;
    started_at: number;
    condition: string;
    title: string;
  };
  runs: { elapsed_seconds: number; condition: string }[];
  result?: {
    manual_seconds: number;
    assisted_seconds: number;
    saved_seconds: number;
    saved_percent: number;
    limitation: string;
  };
};
export default function TrialPage() {
  const [trial, setTrial] = useState<Trial | null>(null),
    [plan, setPlan] = useState<Plan | null>(null),
    [output, setOutput] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [reviewed, setReviewed] = useState(false),
    [now, setNow] = useState(0);
  async function request<T = Trial>(
    path: string,
    body?: unknown,
    method = 'POST',
    revision?: number,
  ): Promise<T> {
    if (!['localhost', '127.0.0.1'].includes(window.location.hostname))
      throw Error(
        'Run EditDNA locally to perform the timed trial. See the source repository for setup.',
      );
    const r = await fetch(api + path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(revision ? { 'If-Match': String(revision) } : {}),
      },
      ...(method === 'GET'
        ? {}
        : { body: body ? JSON.stringify(body) : undefined }),
    });
    const d = (await r.json()) as T & { detail?: string };
    if (!r.ok)
      throw Error(typeof d.detail === 'string' ? d.detail : 'Request failed');
    return d;
  }
  async function sync(t: Trial) {
    setTrial(t);
    localStorage.setItem('editdna-trial', t.id);
    if (t.active) {
      const state: State = await request<State>('/state', undefined, 'GET');
      const p = state.plans.find((p) => p.id === t.active!.plan_id);
      if (p) {
        setPlan(p);
        setOutput(
          state.exports.find(
            (e) => e.plan_id === p.id && e.revision === p.revision,
          )?.id || '',
        );
      }
    }
  }
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await fn();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    const id = localStorage.getItem('editdna-trial');
    if (id)
      void request(`/trials/${id}`, undefined, 'GET')
        .then(sync)
        .catch((e) => setError(String(e)));
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(timer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!trial?.active || trial.status !== 'running') return;
    const timer = setInterval(() => {
      void fetch(api + '/state')
        .then(async (r) => (await r.json()) as State)
        .then((s: State) => {
          const p = s.plans.find((p) => p.id === trial.active!.plan_id);
          if (p)
            setOutput(
              s.exports.find(
                (e) => e.plan_id === p.id && e.revision === p.revision,
              )?.id || '',
            );
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(timer);
  }, [trial]);
  async function save(p: Plan) {
    await run(async () => {
      setPlan(
        await request<Plan>(
          `/plans/${p.id}`,
          { segments: p.segments, visual: { zoom: p.visual?.zoom || 1 } },
          'PATCH',
          p.revision,
        ),
      );
      setOutput('');
      setReviewed(false);
    });
  }
  const active = trial?.status === 'running';
  return (
    <main
      style={{
        maxWidth: 1000,
        margin: 'auto',
        padding: '32px 20px',
        display: 'grid',
        gap: 20,
      }}
    >
      <Link href="/">← EditDNA Studio</Link>
      <h1 style={{ fontSize: 32 }}>The timed editing trial</h1>
      <p>
        Two short tutorials, one manual edit and one EditDNA-assisted edit. Both
        use the same editor and quality target. The clock includes editing,
        rendering, and watching the result. Transcription and profile training
        are already complete.
      </p>
      <section
        style={{ padding: 20, border: '1px solid #435364', borderRadius: 12 }}
      >
        <strong>Your task in both conditions</strong>
        <p>
          Keep all eight unique instructions in order. Keep the later copy of
          each repeated instruction. Leave about 0.12 seconds of silence after
          each phrase, with no trailing silence after the final phrase. Use
          1.10× centered framing. Render, watch the entire output, and check
          that speech and important text remain intact.
        </p>
        <p>
          Manual mode starts with all takes and pauses. Assisted mode starts
          with the learned edit. You can adjust each segment end time and remove
          earlier repeated takes below. A negative saving is a valid result. Do
          not pause the clock or switch tasks mid-run.
        </p>
      </section>
      {error && (
        <p role="alert" style={{ color: '#ffaaa0' }}>
          {error}
        </p>
      )}
      {!trial && (
        <button
          disabled={busy}
          onClick={() => void run(async () => sync(await request('/trials')))}
        >
          Prepare my trial
        </button>
      )}
      {trial && (
        <p>
          Order: {trial.order.join(' → ')}. Completed: {trial.runs.length}/2.
        </p>
      )}
      {trial?.status === 'ready' && (
        <button
          disabled={busy}
          onClick={() =>
            void run(async () => {
              setReviewed(false);
              await sync(await request(`/trials/${trial.id}/begin`));
            })
          }
        >
          Start next task and timer
        </button>
      )}
      {active && plan && (
        <>
          <div
            style={{
              position: 'sticky',
              top: 0,
              background: '#152330',
              padding: 16,
              zIndex: 3,
            }}
          >
            <strong>
              {trial.active?.condition.toUpperCase()} · {trial.active?.title}
            </strong>
            <p aria-live="off">
              Elapsed:{' '}
              {Math.max(0, Math.floor(now - (trial.active?.started_at || now)))}{' '}
              seconds
            </p>
          </div>
          <video
            key={output || plan.asset_id}
            controls
            style={{ width: '100%' }}
            src={
              output
                ? `${api}/exports/${output}/edit.mp4`
                : `${api}/assets/${plan.asset_id}/media`
            }
          >
            <track
              kind="captions"
              srcLang="en"
              label="English"
              src={
                output
                  ? `${api}/exports/${output}/captions.vtt`
                  : `${api}/assets/${plan.asset_id}/captions.vtt`
              }
            />
          </video>
          <p>
            {output
              ? 'Current rendered edit'
              : 'Original recording — render to preview your edits'}
          </p>
          <label>
            Centered framing (1.00–1.40×){' '}
            <input
              aria-label="Trial framing"
              type="number"
              step="0.01"
              min="1"
              max="1.4"
              disabled={busy}
              key={`z${plan.revision}`}
              defaultValue={plan.visual?.zoom || 1}
              onBlur={(e) => {
                const z = Number(e.target.value);
                if (z >= 1 && z <= 1.4 && z !== plan.visual?.zoom)
                  void save({
                    ...plan,
                    visual: { zoom: z, origin: 'user_set' },
                  });
              }}
            />
          </label>
          {plan.segments.map((s, i) => (
            <div
              key={`${s.id}-${plan.revision}`}
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 12,
                padding: 12,
                border: '1px solid #435364',
              }}
            >
              <span style={{ flex: '1 1 300px' }}>
                {i + 1}. {s.text}
              </span>
              <label>
                End (seconds){' '}
                <input
                  style={{ width: 90 }}
                  aria-label={`Segment ${i + 1} end`}
                  type="number"
                  step="0.01"
                  defaultValue={s.end.toFixed(3)}
                  disabled={busy}
                  onBlur={(e) => {
                    const end = Number(e.target.value);
                    if (end !== s.end)
                      void save({
                        ...plan,
                        segments: plan.segments.map((x, j) =>
                          j === i ? { ...x, end } : x,
                        ),
                      });
                  }}
                />
              </label>
              <button
                disabled={busy || plan.segments.length === 1}
                onClick={() =>
                  void save({
                    ...plan,
                    segments: plan.segments.filter((_, j) => j !== i),
                  })
                }
              >
                Remove take {i + 1}
              </button>
            </div>
          ))}
          <button
            disabled={busy || !plan.history.length}
            onClick={() =>
              void run(async () => {
                setPlan(
                  await request<Plan>(
                    `/plans/${plan.id}/undo`,
                    undefined,
                    'POST',
                    plan.revision,
                  ),
                );
                setOutput('');
                setReviewed(false);
              })
            }
          >
            Undo last edit
          </button>
          <button
            disabled={busy}
            onClick={() =>
              void run(async () => {
                await request(`/plans/${plan.id}/export`);
              })
            }
          >
            Render current edit
          </button>
          {output && (
            <>
              <label>
                <input
                  type="checkbox"
                  checked={reviewed}
                  onChange={(e) => setReviewed(e.target.checked)}
                />{' '}
                I watched the full rendered edit: speech is intact, the correct
                takes remain, and framing keeps important content visible.
              </label>
              <button
                disabled={busy || !reviewed}
                onClick={() =>
                  void run(async () =>
                    sync(
                      await request(`/trials/${trial.id}/finish`, { reviewed }),
                    ),
                  )
                }
              >
                Finish task and record time
              </button>
            </>
          )}
        </>
      )}
      {trial?.result && (
        <section>
          <h2>Recorded pilot result</h2>
          <p>
            Manual: {trial.result.manual_seconds}s. Assisted:{' '}
            {trial.result.assisted_seconds}s. Difference:{' '}
            {trial.result.saved_seconds}s ({trial.result.saved_percent}%).
          </p>
          <p>{trial.result.limitation}</p>
          <a
            download="editdna-timed-trial.json"
            href={`data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(trial, null, 2))}`}
          >
            Download timing evidence
          </a>
        </section>
      )}
      <small>
        This is a controlled pilot on owned synthetic footage, not a population
        benchmark. Task order, familiarity, and different tutorial lengths can
        affect the result. Results are stored locally; no timing claim exists
        until you finish both tasks.
      </small>
    </main>
  );
}
