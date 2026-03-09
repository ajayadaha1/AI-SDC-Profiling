import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Collapse,
  Typography,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import ErrorIcon from '@mui/icons-material/Error';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import PsychologyIcon from '@mui/icons-material/Psychology';
import StorageIcon from '@mui/icons-material/Storage';
import DataObjectIcon from '@mui/icons-material/DataObject';
import CodeIcon from '@mui/icons-material/Code';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import type { ThinkingStep, SearchCompleteData, ParsedProfile } from '../../types/chat';

interface ThinkingProcessProps {
  steps: ThinkingStep[];
  isStreaming: boolean;
  parsedProfile: ParsedProfile | null;
  searchResult: SearchCompleteData | null;
}

const chipSx = { fontSize: '0.7rem', height: 22, '& .MuiChip-label': { px: 0.75 } };
const smallChipSx = { fontSize: '0.65rem', height: 20, '& .MuiChip-label': { px: 0.75 } };

function StepIcon({ status }: { status: ThinkingStep['status'] }) {
  if (status === 'done') {
    return <CheckCircleIcon sx={{ fontSize: 18, color: 'success.main' }} />;
  }
  if (status === 'running') {
    return (
      <AutorenewIcon
        sx={{
          fontSize: 18,
          color: 'secondary.main',
          animation: 'thinkingSpin 1s linear infinite',
          '@keyframes thinkingSpin': {
            from: { transform: 'rotate(0deg)' },
            to: { transform: 'rotate(360deg)' },
          },
        }}
      />
    );
  }
  if (status === 'error') {
    return <ErrorIcon sx={{ fontSize: 18, color: 'error.main' }} />;
  }
  return <RadioButtonUncheckedIcon sx={{ fontSize: 18, color: 'text.disabled' }} />;
}

// ---------------------------------------------------------------------------
// Parsed Profile Detail — chips + keywords + reasoning
// ---------------------------------------------------------------------------

function ParsedProfileDetail({ profile }: { profile: ParsedProfile }) {
  const chips: Array<{ label: string; color: 'error' | 'warning' | 'info' | 'default' | 'success' }> = [
    { label: profile.failure_type, color: 'error' },
  ];
  if (profile.mce_bank !== null && profile.mce_bank !== undefined) chips.push({ label: `Bank ${profile.mce_bank}`, color: 'warning' });
  if (profile.raw_defect_type) chips.push({ label: `Defect: ${profile.raw_defect_type}`, color: 'warning' });
  if (profile.error_severity) chips.push({ label: profile.error_severity, color: 'error' });
  if (profile.thermal_state) chips.push({ label: `Thermal: ${profile.thermal_state}`, color: 'info' });
  if (profile.voltage_state) chips.push({ label: `Voltage: ${profile.voltage_state}`, color: 'info' });
  if (profile.boot_stage) chips.push({ label: `Stage: ${profile.boot_stage}`, color: 'default' });
  if (profile.mce_code) chips.push({ label: profile.mce_code, color: 'default' });
  if (profile.mce_code_family) chips.push({ label: `MCE: ${profile.mce_code_family}`, color: 'default' });
  if (profile.frequency_context) chips.push({ label: `Freq: ${profile.frequency_context}`, color: 'default' });
  if (profile.failing_cores) chips.push({ label: `Cores: ${profile.failing_cores}`, color: 'default' });

  const keywords = profile.keywords ?? [];

  return (
    <Box sx={{ ml: 3.5, mt: 0.5 }}>
      {/* Main attribute chips */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {chips.map((c, i) => (
          <Chip key={i} label={c.label} size="small" color={c.color} variant="outlined" sx={chipSx} />
        ))}
        <Chip
          label={`${Math.round((profile.confidence ?? 0) * 100)}% confidence`}
          size="small"
          variant="outlined"
          sx={{ ...chipSx, borderColor: 'success.main', color: 'success.main' }}
        />
      </Box>

      {/* Keywords */}
      {keywords.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.4, mt: 0.5 }}>
          {keywords.map((kw, i) => (
            <Chip key={i} label={kw} size="small" variant="outlined"
              sx={{ ...smallChipSx, borderColor: 'rgba(255,255,255,0.15)', color: 'text.disabled' }} />
          ))}
        </Box>
      )}

      {/* LLM reasoning */}
      {profile.reasoning && (
        <Typography
          variant="caption"
          sx={{ display: 'block', color: 'text.disabled', fontStyle: 'italic', lineHeight: 1.4, mt: 0.5 }}
        >
          {profile.reasoning}
        </Typography>
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Tool Distribution Table — expandable rows with per-source detail
// ---------------------------------------------------------------------------

function ToolDistributionTable({ data }: { data: SearchCompleteData }) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  if (!data.tool_distribution || data.tool_distribution.length === 0) return null;

  return (
    <Box sx={{ mt: 1, ml: 3.5, mb: 0.5 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
        <StorageIcon sx={{ fontSize: 14 }} />
        Snowflake Query Results
      </Typography>
      <Table size="small" sx={{ '& td, & th': { py: 0.25, px: 1, border: 'none', fontSize: '0.75rem' } }}>
        <TableBody>
          {data.tool_distribution.map((row) => {
            const isExpanded = expandedTool === row.tool;
            const hasDetails = (row.details?.length > 0) || (row.banks?.length > 0) || (row.unique_cpus > 0);
            return (
              <TableRow
                key={row.tool}
                sx={{ '&:hover': { bgcolor: 'action.hover' }, cursor: hasDetails ? 'pointer' : 'default' }}
                onClick={() => hasDetails && setExpandedTool(isExpanded ? null : row.tool)}
              >
                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600, color: row.tool === 'other' ? 'text.disabled' : 'secondary.main', width: 140 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                    {hasDetails && (isExpanded
                      ? <KeyboardArrowDownIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                      : <KeyboardArrowRightIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
                    )}
                    {row.tool}
                  </Box>
                </TableCell>
                <TableCell sx={{ width: 80, textAlign: 'right', fontFamily: 'monospace' }}>
                  {row.count.toLocaleString()}
                </TableCell>
                <TableCell sx={{ width: 200 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(row.rate, 100)}
                      sx={{
                        flex: 1,
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'rgba(255,255,255,0.06)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          bgcolor: row.tool === 'other' ? 'text.disabled' : 'secondary.main',
                        },
                      }}
                    />
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', minWidth: 42, textAlign: 'right' }}>
                      {row.rate}%
                    </Typography>
                  </Box>
                  {/* Expandable detail */}
                  <Collapse in={isExpanded} timeout={200}>
                    <Box sx={{ mt: 0.5, pl: 0.5 }}>
                      {row.details?.map((d, i) => (
                        <Typography key={i} variant="caption" sx={{ display: 'block', color: 'text.disabled', fontFamily: 'monospace', fontSize: '0.68rem' }}>
                          {d}
                        </Typography>
                      ))}
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.25 }}>
                        {row.banks?.map((b) => (
                          <Chip key={b} label={b} size="small" variant="outlined"
                            sx={{ ...smallChipSx, borderColor: 'rgba(255,255,255,0.2)' }} />
                        ))}
                        {row.unique_cpus > 0 && (
                          <Typography variant="caption" sx={{ color: 'text.disabled', alignSelf: 'center', fontSize: '0.68rem' }}>
                            {row.unique_cpus.toLocaleString()} unique CPUs
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Collapse>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {/* Per-source summary */}
      {data.per_source_summary?.length > 0 ? (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5, ml: 1 }}>
          {data.per_source_summary.map((src) => (
            <Typography key={src.source} variant="caption"
              sx={{ color: 'text.disabled', fontFamily: 'monospace', fontSize: '0.68rem' }}>
              {src.source}: {src.record_count.toLocaleString()} ({src.tool_count} tools)
            </Typography>
          ))}
        </Box>
      ) : (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5, ml: 1 }}>
          {data.sources?.map((src) => (
            <Chip key={src} label={src} size="small" variant="outlined" sx={smallChipSx} />
          ))}
          <Typography variant="caption" sx={{ color: 'text.disabled', ml: 0.5 }}>
            {data.count?.toLocaleString()} total records
          </Typography>
        </Box>
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Sample Data Table — raw Snowflake records
// ---------------------------------------------------------------------------

function SampleDataTable({ records }: { records?: SearchCompleteData['sample_records'] }) {
  if (!records || records.length === 0) return null;

  const hasBank = records.some((r) => r.bank);
  const hasUc = records.some((r) => r.uc_flag !== undefined && r.uc_flag !== null && r.uc_flag !== '');
  const hasCpus = records.some((r) => r.unique_cpus && r.unique_cpus > 0);
  const hasDefect = records.some((r) => r.defect_type);

  return (
    <Box sx={{ mt: 1, ml: 3.5, mb: 0.5 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
        <DataObjectIcon sx={{ fontSize: 14 }} />
        Sample Snowflake Records ({records.length})
      </Typography>
      <Table size="small" sx={{ '& td, & th': { py: 0.2, px: 0.75, border: 'none', fontSize: '0.7rem' } }}>
        <TableHead>
          <TableRow sx={{ '& th': { color: 'text.disabled', fontWeight: 600, fontSize: '0.65rem' } }}>
            <TableCell>Source</TableCell>
            <TableCell>Tool</TableCell>
            <TableCell sx={{ textAlign: 'right' }}>Count</TableCell>
            {hasBank && <TableCell>Bank</TableCell>}
            {hasDefect && <TableCell>Defect</TableCell>}
            {hasUc && <TableCell>UC</TableCell>}
            {hasCpus && <TableCell sx={{ textAlign: 'right' }}>CPUs</TableCell>}
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((row, i) => (
            <TableRow key={i} sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
              <TableCell>
                <Chip label={row.source.replace('_PMDATA', '').replace('_MCEFAIL', '').replace('_LOGFILES', '')}
                  size="small" variant="outlined"
                  sx={{ ...smallChipSx, borderColor: 'rgba(255,255,255,0.15)' }} />
              </TableCell>
              <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600, color: row.tool === 'other' ? 'text.disabled' : 'secondary.main' }}>
                {row.tool}
              </TableCell>
              <TableCell sx={{ textAlign: 'right', fontFamily: 'monospace' }}>
                {row.count.toLocaleString()}
              </TableCell>
              {hasBank && <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{row.bank ?? '—'}</TableCell>}
              {hasDefect && <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{row.defect_type ?? '—'}</TableCell>}
              {hasUc && <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{row.uc_flag ?? '—'}</TableCell>}
              {hasCpus && (
                <TableCell sx={{ textAlign: 'right', fontFamily: 'monospace', color: 'text.secondary' }}>
                  {row.unique_cpus ? row.unique_cpus.toLocaleString() : '—'}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// LLM Input Preview — what the ranker AI saw
// ---------------------------------------------------------------------------

function LLMInputPreview({ table }: { table?: string }) {
  const [open, setOpen] = useState(false);

  if (!table) return null;

  return (
    <Box sx={{ mt: 1, ml: 3.5, mb: 0.5 }}>
      <Typography
        variant="caption"
        onClick={() => setOpen((prev) => !prev)}
        sx={{
          color: 'text.secondary',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          cursor: 'pointer',
          '&:hover': { color: 'secondary.main' },
        }}
      >
        <CodeIcon sx={{ fontSize: 14 }} />
        What the AI ranker saw
        {open ? <ExpandLessIcon sx={{ fontSize: 14 }} /> : <ExpandMoreIcon sx={{ fontSize: 14 }} />}
      </Typography>
      <Collapse in={open} timeout={200}>
        <Box
          sx={{
            mt: 0.5,
            p: 1,
            bgcolor: 'rgba(0,0,0,0.3)',
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.7rem',
            whiteSpace: 'pre',
            overflow: 'auto',
            maxHeight: 200,
            color: 'text.secondary',
            lineHeight: 1.5,
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          {'Tool                 | Total Fails |  % Share | Sources\n'}
          {table}
        </Box>
      </Collapse>
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main ThinkingProcess component
// ---------------------------------------------------------------------------

export default function ThinkingProcess({ steps, isStreaming, parsedProfile, searchResult }: ThinkingProcessProps) {
  const [expanded, setExpanded] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const startTimeRef = useRef<number>(0);
  const wasStreamingRef = useRef(false);

  // Auto-expand when streaming starts, auto-collapse when it ends
  useEffect(() => {
    if (isStreaming && !wasStreamingRef.current) {
      startTimeRef.current = Date.now();
      setExpanded(true);
      wasStreamingRef.current = true;
    }
    if (!isStreaming && wasStreamingRef.current) {
      wasStreamingRef.current = false;
      // Collapse after a short delay so user sees the final state
      const t = setTimeout(() => setExpanded(false), 1200);
      return () => clearTimeout(t);
    }
  }, [isStreaming]);

  // Tick elapsed timer while streaming
  useEffect(() => {
    if (!isStreaming || startTimeRef.current === 0) return;
    const interval = setInterval(() => {
      setElapsed((Date.now() - startTimeRef.current) / 1000);
    }, 200);
    return () => clearInterval(interval);
  }, [isStreaming]);

  if (steps.length === 0) return null;

  const hasRunning = steps.some((s) => s.status === 'running');
  const doneCount = steps.filter((s) => s.status === 'done').length;
  const allDone = steps.every((s) => s.status === 'done');
  const totalRecords = searchResult?.count ?? 0;
  const numSources = searchResult?.sources?.length ?? 0;

  // Build summary for collapsed header
  const summaryParts: string[] = [];
  summaryParts.push(`${steps.length} step${steps.length !== 1 ? 's' : ''}`);
  if (totalRecords > 0) summaryParts.push(`${totalRecords.toLocaleString()} records`);
  if (numSources > 0) summaryParts.push(`${numSources} source${numSources !== 1 ? 's' : ''}`);
  if (elapsed > 0) summaryParts.push(`${elapsed.toFixed(1)}s`);

  const headerLabel = hasRunning
    ? steps.find((s) => s.status === 'running')?.label ?? 'Thinking...'
    : allDone
      ? `Analyzed in ${summaryParts.join(' \u00b7 ')}`
      : 'AI is thinking...';

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 1 }}>
      <Box
        sx={{
          borderRadius: 2,
          border: '1px solid',
          borderColor: hasRunning ? 'rgba(0, 191, 165, 0.35)' : 'divider',
          bgcolor: 'rgba(0,0,0,0.15)',
          overflow: 'hidden',
          transition: 'border-color 0.4s ease',
        }}
      >
        {/* Header — always visible, clickable to toggle */}
        <Box
          onClick={() => setExpanded((prev) => !prev)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            px: 1.5,
            py: 0.75,
            cursor: 'pointer',
            userSelect: 'none',
            '&:hover': { bgcolor: 'action.hover' },
          }}
        >
          {hasRunning ? (
            <PsychologyIcon
              sx={{
                fontSize: 20,
                color: 'secondary.main',
                animation: 'thinkingPulse 1.5s ease-in-out infinite',
                '@keyframes thinkingPulse': {
                  '0%, 100%': { opacity: 1, transform: 'scale(1)' },
                  '50%': { opacity: 0.4, transform: 'scale(1.1)' },
                },
              }}
            />
          ) : (
            <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />
          )}

          <Typography
            variant="body2"
            sx={{
              flex: 1,
              fontWeight: 600,
              fontSize: '0.82rem',
              color: hasRunning ? 'secondary.main' : 'text.secondary',
            }}
          >
            {headerLabel}
          </Typography>

          {/* Elapsed timer during streaming */}
          {hasRunning && elapsed > 0 && (
            <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace', mr: 0.5 }}>
              {elapsed.toFixed(1)}s
            </Typography>
          )}

          {/* Step progress dots */}
          <Box sx={{ display: 'flex', gap: 0.5, mr: 0.5 }}>
            {steps.map((s) => (
              <Box
                key={s.id}
                sx={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  bgcolor: s.status === 'done' ? 'success.main'
                    : s.status === 'running' ? 'secondary.main'
                      : 'text.disabled',
                  ...(s.status === 'running' && {
                    animation: 'thinkingDot 1s ease-in-out infinite',
                    '@keyframes thinkingDot': {
                      '0%, 100%': { opacity: 1, transform: 'scale(1)' },
                      '50%': { opacity: 0.4, transform: 'scale(0.7)' },
                    },
                  }),
                }}
              />
            ))}
          </Box>

          <IconButton size="small" sx={{ p: 0.25, color: 'text.disabled' }}>
            {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
          </IconButton>
        </Box>

        {/* Indeterminate progress bar while running */}
        {hasRunning && (
          <LinearProgress
            variant="indeterminate"
            sx={{
              height: 2,
              bgcolor: 'transparent',
              '& .MuiLinearProgress-bar': { bgcolor: 'secondary.main' },
            }}
          />
        )}

        {/* Expanded content — detailed steps */}
        <Collapse in={expanded} timeout={300}>
          <Box sx={{ borderTop: '1px solid rgba(255,255,255,0.06)', px: 1.5, py: 1, display: 'flex', flexDirection: 'column', gap: 0.75 }}>
            {steps.map((step) => (
              <Box
                key={step.id}
                sx={{
                  animation: 'thinkingFadeIn 0.3s ease-out',
                  '@keyframes thinkingFadeIn': {
                    '0%': { opacity: 0, transform: 'translateY(-4px)' },
                    '100%': { opacity: 1, transform: 'translateY(0)' },
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StepIcon status={step.status} />
                  <Typography
                    variant="body2"
                    sx={{
                      flex: 1,
                      fontWeight: step.status === 'running' ? 600 : 400,
                      fontSize: '0.8rem',
                      color: step.status === 'running' ? 'text.primary' : 'text.secondary',
                    }}
                  >
                    {step.label}
                  </Typography>
                </Box>
                {step.detail && (
                  <Typography
                    variant="caption"
                    sx={{ ml: 3.5, display: 'block', color: 'text.disabled', fontStyle: 'italic', lineHeight: 1.4 }}
                  >
                    {step.detail}
                  </Typography>
                )}

                {/* Parsed profile chips after parsing_complete */}
                {step.id === 'parse' && step.status === 'done' && parsedProfile && (
                  <ParsedProfileDetail profile={parsedProfile} />
                )}

                {/* Snowflake data after search_complete */}
                {step.id === 'search' && step.status === 'done' && searchResult && (
                  <>
                    <ToolDistributionTable data={searchResult} />
                    <SampleDataTable records={searchResult.sample_records} />
                    <LLMInputPreview table={searchResult.formatted_command_table} />
                  </>
                )}
              </Box>
            ))}
          </Box>
        </Collapse>
      </Box>
    </Box>
  );
}
