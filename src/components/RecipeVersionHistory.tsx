import React, { useEffect, useState } from 'react';
import { recipeApi } from '../services/api.ts';
import { RecipeVersion, RecipeVersionDiff } from '../types/bread.ts';

interface Props {
  recipeId: string;
  currentVersionId: string;
}

type PanelState =
  | { type: 'none' }
  | { type: 'view'; version: RecipeVersion }
  | { type: 'diff'; v1: RecipeVersion; v2: RecipeVersion; diff: RecipeVersionDiff | null; loading: boolean };

const RecipeVersionHistory: React.FC<Props> = ({ recipeId, currentVersionId }) => {
  const [versions, setVersions] = useState<RecipeVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [panel, setPanel] = useState<PanelState>({ type: 'none' });
  const [compareFrom, setCompareFrom] = useState<RecipeVersion | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setPanel({ type: 'none' });
    setCompareFrom(null);
    recipeApi
      .getVersions(recipeId)
      .then(setVersions)
      .catch(() => setError('Failed to load version history'))
      .finally(() => setLoading(false));
  }, [recipeId]);

  const handleView = (version: RecipeVersion) => {
    setPanel({ type: 'view', version });
    setCompareFrom(null);
  };

  const handleCompareSelect = async (version: RecipeVersion) => {
    if (!compareFrom) {
      setCompareFrom(version);
      return;
    }
    if (compareFrom.id === version.id) {
      setCompareFrom(null);
      return;
    }
    const [v1, v2] = compareFrom.version_number < version.version_number
      ? [compareFrom, version]
      : [version, compareFrom];
    setPanel({ type: 'diff', v1, v2, diff: null, loading: true });
    setCompareFrom(null);
    try {
      const diff = await recipeApi.getVersionDiff(recipeId, v1.id, v2.id);
      setPanel({ type: 'diff', v1, v2, diff, loading: false });
    } catch {
      setPanel({ type: 'diff', v1, v2, diff: null, loading: false });
    }
  };

  const summarizeChanges = (version: RecipeVersion): string => {
    const s = version.change_summary;
    if (!s) return '';
    const parts: string[] = [];
    const ingAdded = s.ingredients_added ?? 0;
    const ingRemoved = s.ingredients_removed ?? 0;
    const ingModified = s.ingredients_modified ?? 0;
    const stepsAdded = s.steps_added ?? 0;
    const stepsRemoved = s.steps_removed ?? 0;
    const stepsModified = s.steps_modified ?? 0;
    if (ingAdded) parts.push(`+${ingAdded} ingredient${ingAdded > 1 ? 's' : ''}`);
    if (ingRemoved) parts.push(`-${ingRemoved} ingredient${ingRemoved > 1 ? 's' : ''}`);
    if (ingModified) parts.push(`~${ingModified} modified`);
    if (stepsAdded) parts.push(`+${stepsAdded} step${stepsAdded > 1 ? 's' : ''}`);
    if (stepsRemoved) parts.push(`-${stepsRemoved} step${stepsRemoved > 1 ? 's' : ''}`);
    if (stepsModified) parts.push(`~${stepsModified} step${stepsModified > 1 ? 's' : ''} modified`);
    return parts.join(', ');
  };

  if (loading) return <p className="text-sm text-gray-500 mt-4">Loading version history…</p>;
  if (error) return <p className="text-sm text-red-500 mt-4">{error}</p>;
  if (versions.length === 0) return null;

  return (
    <div className="mt-6 border-t pt-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Version History</h3>

      {compareFrom && (
        <div className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded px-3 py-1.5 mb-3">
          Selected v{compareFrom.version_number} — click another version to compare
        </div>
      )}

      <div className="space-y-1">
        {versions.map((v) => {
          const isCurrent = v.id === currentVersionId;
          const isCompareFrom = compareFrom?.id === v.id;
          return (
            <div
              key={v.id}
              className={`flex items-start justify-between rounded px-3 py-2 text-sm ${
                isCompareFrom ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-800">v{v.version_number}</span>
                  {isCurrent && (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">current</span>
                  )}
                  {v.version_number === 1 && !isCurrent && (
                    <span className="text-xs text-gray-400">initial</span>
                  )}
                  <span className="text-xs text-gray-400">
                    {new Date(v.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
                {v.version_number > 1 && (
                  <div className="text-xs text-gray-500 mt-0.5">{summarizeChanges(v)}</div>
                )}
              </div>
              <div className="flex gap-1.5 ml-2 shrink-0">
                <button
                  onClick={() => handleView(v)}
                  className="text-xs text-blue-600 hover:text-blue-800 px-2 py-0.5 border border-blue-200 rounded hover:bg-blue-50"
                >
                  View
                </button>
                {versions.length > 1 && (
                  <button
                    onClick={() => handleCompareSelect(v)}
                    className={`text-xs px-2 py-0.5 border rounded ${
                      isCompareFrom
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'text-gray-600 hover:text-gray-800 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {isCompareFrom ? 'Cancel' : 'Compare'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail panel */}
      {panel.type !== 'none' && (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <div className="flex items-center justify-between bg-gray-50 px-4 py-2 border-b">
            <span className="text-sm font-medium text-gray-700">
              {panel.type === 'view'
                ? `v${panel.version.version_number} — full recipe`
                : panel.type === 'diff'
                ? `v${panel.v1.version_number} → v${panel.v2.version_number} diff`
                : ''}
            </span>
            <button
              onClick={() => setPanel({ type: 'none' })}
              className="text-gray-400 hover:text-gray-600 text-lg leading-none"
            >
              ✕
            </button>
          </div>

          <div className="p-4 text-sm">
            {panel.type === 'view' && <VersionDetail version={panel.version} />}
            {panel.type === 'diff' && panel.loading && (
              <p className="text-gray-500">Loading diff…</p>
            )}
            {panel.type === 'diff' && !panel.loading && panel.diff && (
              <DiffPanel diff={panel.diff} />
            )}
            {panel.type === 'diff' && !panel.loading && !panel.diff && (
              <p className="text-red-500">Failed to load diff.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const VersionDetail: React.FC<{ version: RecipeVersion }> = ({ version }) => (
  <div className="space-y-4">
    <div>
      <h4 className="font-medium text-gray-700 mb-2">Ingredients</h4>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-500 border-b">
            <th className="text-left py-1 pr-4">Name</th>
            <th className="text-left py-1 pr-4">Amount</th>
            <th className="text-left py-1 pr-4">Unit</th>
            <th className="text-left py-1">Type</th>
          </tr>
        </thead>
        <tbody>
          {version.ingredients.map((ing: any, i: number) => (
            <tr key={ing.id ?? i} className="border-b border-gray-50">
              <td className="py-1 pr-4 text-gray-800">{ing.name}</td>
              <td className="py-1 pr-4 text-gray-600">{ing.amount}</td>
              <td className="py-1 pr-4 text-gray-600">{ing.unit}</td>
              <td className="py-1 text-gray-500">{ing.type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <div>
      <h4 className="font-medium text-gray-700 mb-2">Instructions</h4>
      <ol className="list-decimal list-inside space-y-1 text-gray-700">
        {version.instructions.map((step: any, i: number) => (
          <li key={step.id ?? i}>{step.instruction}</li>
        ))}
      </ol>
    </div>
  </div>
);

const DiffPanel: React.FC<{ diff: RecipeVersionDiff }> = ({ diff }) => {
  const { ingredient_changes: ic, step_changes: sc } = diff;

  const hasIngredientChanges =
    ic.added.length > 0 || ic.removed.length > 0 || ic.modified.length > 0;
  const hasStepChanges =
    sc.added.length > 0 || sc.removed.length > 0 || sc.modified.length > 0;

  return (
    <div className="space-y-4 font-mono text-xs">
      {!hasIngredientChanges && !hasStepChanges && (
        <p className="text-gray-400">No changes between these versions.</p>
      )}

      {hasIngredientChanges && (
        <div>
          <p className="font-semibold text-gray-600 mb-1 font-sans">Ingredients</p>
          {ic.added.map((ing: any, i: number) => (
            <div key={i} className="bg-green-50 text-green-800 px-2 py-1 rounded mb-0.5">
              + {ing.amount}{ing.unit} {ing.name}
            </div>
          ))}
          {ic.removed.map((ing: any, i: number) => (
            <div key={i} className="bg-red-50 text-red-800 px-2 py-1 rounded mb-0.5">
              - {ing.amount}{ing.unit} {ing.name}
            </div>
          ))}
          {ic.modified.map((m: any, i: number) => (
            <div key={i} className="bg-amber-50 text-amber-900 px-2 py-1 rounded mb-0.5">
              <div className="text-red-700">- {m.old.amount}{m.old.unit} {m.old.name}</div>
              <div className="text-green-700">+ {m.new.amount}{m.new.unit} {m.new.name}</div>
            </div>
          ))}
        </div>
      )}

      {hasStepChanges && (
        <div>
          <p className="font-semibold text-gray-600 mb-1 font-sans">Instructions</p>
          {sc.added.map((step: any, i: number) => (
            <div key={i} className="bg-green-50 text-green-800 px-2 py-1 rounded mb-0.5">
              + {step.instruction}
            </div>
          ))}
          {sc.removed.map((step: any, i: number) => (
            <div key={i} className="bg-red-50 text-red-800 px-2 py-1 rounded mb-0.5">
              - {step.instruction}
            </div>
          ))}
          {sc.modified.map((m: any, i: number) => (
            <div key={i} className="bg-amber-50 text-amber-900 px-2 py-1 rounded mb-0.5">
              <div className="text-red-700">- {m.old.instruction}</div>
              <div className="text-green-700">+ {m.new.instruction}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecipeVersionHistory;
