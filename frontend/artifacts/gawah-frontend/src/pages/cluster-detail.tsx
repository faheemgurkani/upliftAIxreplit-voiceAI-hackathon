import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'wouter';
import { fetchCluster } from '@/lib/api';
import { PageShell } from '@/components/layout/page-shell';
import { ScoreBar, DisclaimerBadge } from '@/components/badges';

export default function ClusterDetailPage() {
  const { clusterId } = useParams<{ clusterId: string }>();

  const { data: cluster, isLoading, error } = useQuery({
    queryKey: ['cluster', clusterId],
    queryFn: () => fetchCluster(clusterId as string),
    enabled: !!clusterId,
  });

  if (isLoading) {
    return (
      <PageShell>
        <div className="state-panel" style={{ margin: 32, border: 'none' }}>
          <div className="spinner" />
          <div className="pager-meta">Loading cluster</div>
        </div>
      </PageShell>
    );
  }

  if (error || !cluster) {
    return (
      <PageShell>
        <div className="page-content">
          <div className="insight" style={{ borderColor: 'var(--e-warn)' }}>
            <span className="insight-lbl">ERROR</span>
            Cluster not found.
            <div style={{ marginTop: 16 }}>
              <Link href="/clusters" className="cta-btn">
                <span className="cta-sq">←</span>
                <span className="cta-lbl">Back to Clusters</span>
              </Link>
            </div>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="disclaimer-sticky">
        <DisclaimerBadge />
      </div>

      <div className="page-content page-stack">
        <div className="page-header">
          <div className="section-eyebrow breadcrumb">
            <Link href="/clusters">CLUSTERS</Link>
            <span className="sep">/</span>
            <span className="text-e-accent">{cluster.id.substring(0, 8)}...</span>
          </div>
          <h1 className="section-title" style={{ marginTop: 8 }}>
            {cluster.cluster_label}
          </h1>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div className="badge-e badge-gray" style={{ fontSize: 14, padding: '4px 12px' }}>
              {cluster.statement_count} STATEMENTS
            </div>
            {cluster.composite_score != null && (
              <div
                className="hud"
                style={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'center',
                  padding: '8px 16px',
                  gap: 16,
                  minHeight: 'auto',
                }}
              >
                <span className="hud-k" style={{ marginBottom: 0 }}>
                  COMPOSITE
                </span>
                <span className="hud-v accent" style={{ fontSize: 32 }}>
                  {Math.round(cluster.composite_score * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {cluster.collusion_warning && (
          <div className="insight" style={{ borderColor: 'var(--e-yellow)' }}>
            <span className="insight-lbl" style={{ color: 'var(--e-yellow)' }}>
              COLLUSION CHECK
            </span>
            Unusually high agreement detected across all fields. This pattern requires manual
            verification before use. Do not interpret as strong corroboration.
          </div>
        )}

        <div className="bento">
          <div className="bento-h">
            <span className="dot dot-o" />
            FIELD.CORROBORATION
          </div>
          <div className="bento-body" style={{ padding: 0 }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="brutal" style={{ border: 'none' }}>
                <thead>
                  <tr>
                    <th>FIELD</th>
                    <th>STATUS</th>
                    <th>SCORE</th>
                    <th>VALUES</th>
                    <th>DETAIL</th>
                  </tr>
                </thead>
                <tbody>
                  {cluster.field_results.map((fr, idx) => {
                    let statusColor = 'gray';
                    if (fr.status === 'agreement') statusColor = 'teal';
                    else if (fr.status === 'partial_agreement') statusColor = 'amber';
                    else if (fr.status === 'conflict') statusColor = 'red';
                    else if (fr.status === 'collusion_warning') statusColor = 'yellow';

                    return (
                      <tr key={idx}>
                        <td className="first">{fr.field}</td>
                        <td>
                          <span className={`badge-e badge-${statusColor}`}>
                            {fr.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td style={{ minWidth: 150 }}>
                          <ScoreBar score={fr.agreement_score} />
                        </td>
                        <td>{fr.values?.join(' | ') || '-'}</td>
                        <td className="text-e-muted" style={{ fontSize: 13 }}>
                          {fr.conflict_detail || fr.note || '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div
              style={{
                padding: 16,
                borderTop: '2px solid var(--e-fg)',
                background: 'var(--e-paper)',
              }}
            >
              <DisclaimerBadge />
            </div>
          </div>
        </div>

        {cluster.consensus_recommendation && (
          <div className="insight">
            <span className="insight-lbl">CONSENSUS RECOMMENDATION</span>
            {cluster.consensus_recommendation}
          </div>
        )}

        <div className="bento">
          <div className="bento-h">
            <span className="dot dot-k" />
            LINKED.STATEMENTS
          </div>
          <div className="bento-body" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {cluster.linked_statements.map((stmt) => (
              <Link
                key={stmt.ref_code}
                href={`/dashboard/${stmt.ref_code}`}
                className="cta-btn cta-ghost"
              >
                <span className="cta-sq">#</span>
                <span className="cta-lbl">{stmt.ref_code}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
