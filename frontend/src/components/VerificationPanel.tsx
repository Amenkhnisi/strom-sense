import React, { useState } from 'react';
import { Check, Edit3, AlertTriangle, CheckCircle2, XCircle, Calendar, Save, X, Sparkles } from 'lucide-react';
import type { ParsedInvoiceData, FieldValue, BillingPeriod } from '../types/ParsedInvoiceData';


interface VerificationPanelProps {
    data: ParsedInvoiceData;
    onSave?: (updated: ParsedInvoiceData) => void;
}

const VerificationPanel: React.FC<VerificationPanelProps> = ({ data, onSave }) => {
    const [editableData, setEditableData] = useState<ParsedInvoiceData>(data);
    const [editing, setEditing] = useState(false);
    const [changedFields, setChangedFields] = useState<Set<string>>(new Set());

    const handleFieldChange = (key: keyof ParsedInvoiceData, value: string) => {
        setEditableData({
            ...editableData,
            [key]: {
                ...(editableData[key] as FieldValue),
                normalized: value,
            },
        });
        setChangedFields(new Set([...changedFields, key]));
    };

    const handleBillingPeriodChange = (field: 'start_date' | 'end_date', value: string) => {
        const current = editableData.billingPeriod?.normalized || { start_date: null, end_date: null };
        setEditableData({
            ...editableData,
            billingPeriod: {
                ...(editableData.billingPeriod as FieldValue<BillingPeriod>),
                normalized: {
                    ...current,
                    [field]: value,
                },
            },
        });
        setChangedFields(new Set([...changedFields, 'billingPeriod']));
    };

    const handleSave = () => {
        setEditing(false);
        setChangedFields(new Set());
        onSave?.(editableData);
    };

    const handleCancel = () => {
        setEditableData(data);
        setEditing(false);
        setChangedFields(new Set());
    };

    const getConfidenceColor = (confidence: number) => {
        if (confidence > 0.9) return 'text-emerald-600 bg-emerald-50';
        if (confidence > 0.7) return 'text-amber-600 bg-amber-50';
        return 'text-red-600 bg-red-50';
    };

    const getConfidenceBadge = (confidence: number) => {
        if (confidence > 0.9) return { icon: CheckCircle2, label: 'High', color: 'bg-emerald-500' };
        if (confidence > 0.7) return { icon: AlertTriangle, label: 'Medium', color: 'bg-amber-500' };
        return { icon: XCircle, label: 'Low', color: 'bg-red-500' };
    };

    const formatFieldName = (key: string) => {
        return key
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, (str) => str.toUpperCase())
            .trim();
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    };

    const renderField = (key: string, field: FieldValue<any>) => {
        const Badge = getConfidenceBadge(field.confidence);
        const isChanged = changedFields.has(key);
        const confidenceColor = getConfidenceColor(field.confidence);

        return (
            <div
                key={key}
                className={`group relative bg-white border-2 rounded-2xl p-5 transition-all duration-300 hover:shadow-xl ${isChanged ? 'border-blue-400 bg-blue-50/30' : 'border-slate-200 hover:border-slate-300'
                    }`}
            >
                {/* Changed Indicator */}
                {isChanged && (
                    <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg animate-pulse">
                        Modified
                    </div>
                )}

                {/* Field Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-700">{formatFieldName(key)}</h3>
                        {field.confidence < 0.75 && !editing && (
                            <div className="relative group/tooltip">
                                <AlertTriangle className="w-4 h-4 text-amber-500 animate-pulse" />
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                                    Please verify this field
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Confidence Badge */}
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${confidenceColor} text-xs font-bold`}>
                        <Badge.icon className="w-3.5 h-3.5" />
                        <span>{(field.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>

                {/* Field Value */}
                {key === 'billingPeriod' && field.normalized ? (
                    <div className="space-y-3">
                        {editing ? (
                            <>
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        Start Date
                                    </label>
                                    <input
                                        type="date"
                                        value={field.normalized.start_date || ''}
                                        onChange={(e) => handleBillingPeriodChange('start_date', e.target.value)}
                                        className="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all text-sm font-medium"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        End Date
                                    </label>
                                    <input
                                        type="date"
                                        value={field.normalized.end_date || ''}
                                        onChange={(e) => handleBillingPeriodChange('end_date', e.target.value)}
                                        className="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all text-sm font-medium"
                                    />
                                </div>
                            </>
                        ) : (
                            <div className="flex items-center justify-between bg-slate-50 rounded-xl px-4 py-3">
                                <span className="text-sm font-semibold text-slate-700">
                                    {formatDate(field.normalized.start_date)}
                                </span>
                                <div className="w-8 h-0.5 bg-slate-300 rounded-full"></div>
                                <span className="text-sm font-semibold text-slate-700">
                                    {formatDate(field.normalized.end_date)}
                                </span>
                            </div>
                        )}
                    </div>
                ) : editing ? (
                    <input
                        type="text"
                        value={field.normalized ?? ''}
                        onChange={(e) => handleFieldChange(key as keyof ParsedInvoiceData, e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all font-medium text-slate-800"
                        placeholder={`Enter ${formatFieldName(key).toLowerCase()}`}
                    />
                ) : (
                    <div className="mt-2">
                        <p className="text-lg font-bold text-slate-900">
                            {field.normalized ?? (
                                <span className="text-slate-400 italic text-base font-normal">No data available</span>
                            )}
                        </p>
                        {field.raw && field.raw !== field.normalized && (
                            <p className="text-xs text-slate-500 mt-1 font-mono bg-slate-100 px-2 py-1 rounded inline-block">
                                Raw: {field.raw}
                            </p>
                        )}
                    </div>
                )}
            </div>
        );
    };

    // Calculate statistics
    const fields = Object.entries(editableData).filter(([key]) => key !== 'supplier');
    const avgConfidence = fields.reduce((acc, [, value]) => acc + ((value as FieldValue)?.confidence || 0), 0) / fields.length;
    const lowConfidenceCount = fields.filter(([, value]) => ((value as FieldValue)?.confidence || 0) < 0.75).length;
    const highConfidenceCount = fields.filter(([, value]) => ((value as FieldValue)?.confidence || 0) > 0.9).length;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header Card */}
                <div className="bg-white rounded-3xl shadow-2xl border-2 border-slate-200 p-8 mb-8">
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                        {/* Title & Stats */}
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-3 rounded-2xl">
                                    <Sparkles className="w-8 h-8 text-white" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                                        Verification Panel
                                    </h1>
                                    <p className="text-slate-500 text-sm mt-1">Review and edit extracted invoice data</p>
                                </div>
                            </div>

                            {/* Statistics */}
                            <div className="flex flex-wrap gap-3">
                                <div className="flex items-center gap-2 bg-emerald-50 px-4 py-2 rounded-xl border border-emerald-200">
                                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                                    <span className="text-sm font-bold text-emerald-700">
                                        {highConfidenceCount} High Confidence
                                    </span>
                                </div>
                                {lowConfidenceCount > 0 && (
                                    <div className="flex items-center gap-2 bg-amber-50 px-4 py-2 rounded-xl border border-amber-200">
                                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                                        <span className="text-sm font-bold text-amber-700">
                                            {lowConfidenceCount} Need Review
                                        </span>
                                    </div>
                                )}
                                <div className="flex items-center gap-2 bg-blue-50 px-4 py-2 rounded-xl border border-blue-200">
                                    <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                                        <span className="text-white text-xs font-bold">{(avgConfidence * 100).toFixed(0)}%</span>
                                    </div>
                                    <span className="text-sm font-bold text-blue-700">
                                        Avg. Confidence
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-3">
                            {editing ? (
                                <>
                                    <button
                                        onClick={handleCancel}
                                        className="flex items-center gap-2 px-6 py-3 border-2 border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 transition-all font-semibold"
                                    >
                                        <X className="w-5 h-5" />
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-green-600 text-white rounded-xl hover:from-emerald-700 hover:to-green-700 transition-all font-semibold shadow-lg shadow-emerald-500/30"
                                    >
                                        <Save className="w-5 h-5" />
                                        Save Changes
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={() => setEditing(true)}
                                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-semibold shadow-lg shadow-blue-500/30"
                                >
                                    <Edit3 className="w-5 h-5" />
                                    Edit Data
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Fields Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Object.entries(editableData)
                        .filter(([key]) => key !== 'supplier')
                        .map(([key, value]) => {
                            const field = value as FieldValue<any>;
                            if (!field) return null;
                            return renderField(key, field);
                        })}
                </div>

                {/* Edit Mode Notice */}
                {editing && (
                    <div className="mt-8 bg-blue-50 border-2 border-blue-200 rounded-2xl p-6">
                        <div className="flex items-start gap-4">
                            <div className="bg-blue-600 p-2 rounded-lg">
                                <Edit3 className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-blue-900 mb-1">Edit Mode Active</h3>
                                <p className="text-blue-700 text-sm">
                                    Make your changes to the fields above. Modified fields will be highlighted.
                                    Click "Save Changes" when done or "Cancel" to discard changes.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Low Confidence Warning */}
                {lowConfidenceCount > 0 && !editing && (
                    <div className="mt-8 bg-amber-50 border-2 border-amber-200 rounded-2xl p-6">
                        <div className="flex items-start gap-4">
                            <div className="bg-amber-600 p-2 rounded-lg">
                                <AlertTriangle className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-amber-900 mb-1">Attention Required</h3>
                                <p className="text-amber-700 text-sm">
                                    {lowConfidenceCount} field{lowConfidenceCount > 1 ? 's' : ''} ha{lowConfidenceCount > 1 ? 've' : 's'} low confidence scores.
                                    Please review and verify the data before saving.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// Demo Component with Sample Data
export default VerificationPanel