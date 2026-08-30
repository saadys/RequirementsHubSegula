import React, { useState, useEffect } from 'react';
import { 
  Send, 
  UploadCloud, 
  FileText, 
  Trash2, 
  Loader2, 
  User, 
  Mail, 
  Briefcase, 
  HelpCircle, 
  AlertCircle,
  Clock,
  Sparkles,
  Zap
} from 'lucide-react';
import { fetchDepartmentFields, submitRequest, submitRequestAsync, submitRequestWithUpload, pollSubmissionUntilComplete } from '../api/client';
import DepartmentSelector from './DepartmentSelector';
import SubmissionStream from './SubmissionStream';

export default function SubmissionForm({ departments, onSubmissionSuccess, onOpenClarification }) {
  const [selectedDept, setSelectedDept] = useState('corporate_support');
  const [dynamicFields, setDynamicFields] = useState([]);
  const [loadingFields, setLoadingFields] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [streamMode, setStreamMode] = useState(true);
  const [streamingPayload, setStreamingPayload] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    project_name: '',
    team_contact_name: '',
    team_contact_email: '',
    problem_description: '',
    current_process: '',
    expected_outcome: '',
    data_description: '',
    deadline_urgency: 'medium',
    department_specific: {
      service_area: 'hr',
      target_users: 'employees',
      has_existing_system: false,
    },
  });

  // PDF File state
  const [attachedFile, setAttachedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Mapping of Service Area to relevant Target Users options
  const SERVICE_AREA_TARGET_USERS = {
    hr: ['all_employees', 'hr_team', 'managers', 'candidates', 'other'],
    it: ['all_employees', 'it_support_team', 'developers_tech', 'managers', 'other'],
    finance: ['all_employees', 'finance_team', 'managers', 'auditors', 'other'],
    legal: ['all_employees', 'legal_team', 'managers', 'external_partners', 'other'],
    facilities: ['all_employees', 'facilities_team', 'site_managers', 'other'],
    communication: ['all_employees', 'communication_team', 'external_public', 'other'],
    other: ['all_employees', 'department_team', 'managers', 'other'],
  };

  // Fetch department-specific fields when department changes
  useEffect(() => {
    async function loadFields() {
      try {
        setLoadingFields(true);
        const res = await fetchDepartmentFields(selectedDept);
        setDynamicFields(res.specific_fields || []);
      } catch (err) {
        console.warn('Using default dynamic fields fallback');
        setDynamicFields([
          { name: 'service_area', label: 'Service Area', type: 'select', options: ['hr', 'it', 'finance', 'legal', 'facilities', 'communication', 'other'], required: true },
          { name: 'target_users', label: 'Target Users', type: 'select', options: ['all_employees', 'hr_team', 'managers', 'candidates', 'other'], required: true },
          { name: 'has_existing_system', label: 'Has Existing System?', type: 'boolean', required: false },
        ]);
      } finally {
        setLoadingFields(false);
      }
    }

    loadFields();
  }, [selectedDept]);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleDeptSpecificChange = (field, value) => {
    setFormData((prev) => {
      const updatedDeptSpecific = {
        ...prev.department_specific,
        [field]: value,
      };

      // If Service Area changes, filter and auto-reset Target Users to first valid option
      if (field === 'service_area') {
        const allowedTargets = SERVICE_AREA_TARGET_USERS[value] || SERVICE_AREA_TARGET_USERS.other;
        if (!allowedTargets.includes(updatedDeptSpecific.target_users)) {
          updatedDeptSpecific.target_users = allowedTargets[0];
        }
      }

      return {
        ...prev,
        department_specific: updatedDeptSpecific,
      };
    });
  };

  // Drag & drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setAttachedFile(file);
        setError(null);
      } else {
        setError('Only PDF specification documents are supported.');
      }
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setAttachedFile(file);
        setError(null);
      } else {
        setError('Only PDF specification documents are supported.');
      }
    }
  };

  const isFormValid = Boolean(
    formData.project_name?.trim() &&
    formData.team_contact_name?.trim() &&
    formData.team_contact_email?.trim() &&
    formData.problem_description?.trim() &&
    formData.current_process?.trim() &&
    formData.expected_outcome?.trim() &&
    formData.data_description?.trim() &&
    formData.deadline_urgency
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Form validation
    if (!formData.project_name.trim()) {
      setError('Please enter a Project Name.');
      return;
    }
    if (!formData.team_contact_name.trim() || !formData.team_contact_email.trim()) {
      setError('Please provide contact person name and email.');
      return;
    }
    if (!formData.problem_description.trim()) {
      setError('Please describe the problem you want AI to solve.');
      return;
    }
    if (!formData.current_process.trim()) {
      setError('Please describe the Current Manual Process.');
      return;
    }
    if (!formData.expected_outcome.trim()) {
      setError('Please specify the Expected Outcome / Target Benefit.');
      return;
    }
    if (!formData.data_description.trim()) {
      setError('Please describe the Available Data.');
      return;
    }
    if (!formData.deadline_urgency) {
      setError('Please select Project Urgency / Deadline.');
      return;
    }

    const payload = {
      ...formData,
      department: selectedDept,
    };

    // If Real-Time Streaming is active (and no PDF file upload attached), fast-register queue
    if (streamMode && !attachedFile) {
      try {
        setSubmitting(true);
        const regRes = await submitRequestAsync(payload);
        const reqId = regRes.request_id;
        const initQueue = regRes.queue || regRes;
        setStreamingPayload({
          ...payload,
          _registeredRequestId: reqId,
          _initialQueue: initQueue,
        });
      } catch (err) {
        setError(err.message || 'Failed to submit AI project request');
      } finally {
        setSubmitting(false);
      }
      return;
    }

    try {
      setSubmitting(true);
      let result;

      if (attachedFile) {
        // Submit via multipart form upload endpoint
        const uploadData = new FormData();
        uploadData.append('form_data_json', JSON.stringify(payload));
        uploadData.append('file', attachedFile);
        result = await submitRequestWithUpload(uploadData);
      } else {
        // Submit standard JSON payload
        result = await submitRequest(payload);
      }

      // If response status is PENDING, poll until background pipeline completes
      if (result && result.status === 'PENDING' && result.request_id) {
        result = await pollSubmissionUntilComplete(result.request_id);
      }

      onSubmissionSuccess(result);
    } catch (err) {
      setError(err.message || 'Failed to submit AI project request');
    } finally {
      setSubmitting(false);
    }
  };

  if (streamingPayload) {
    return (
      <SubmissionStream
        payload={streamingPayload}
        onComplete={onSubmissionSuccess}
        onAnswerClarification={(res) => {
          const reqId = res?.request_id || res?.id;
          if (onOpenClarification && reqId) {
            onOpenClarification(reqId);
          } else {
            onSubmissionSuccess(res);
          }
        }}
        onCancel={() => setStreamingPayload(null)}
      />
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles color="#3B82F6" size={24} /> Submit New AI Project Requirement
        </h2>
        <p style={{ fontSize: '0.88rem', color: '#94A3B8', marginTop: '4px' }}>
          Fill out the project details below to trigger automated technical feasibility scoring and Cahier des Charges generation.
        </p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#F87171', padding: '12px 16px', borderRadius: '10px', fontSize: '0.88rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Department Selector */}
        <DepartmentSelector 
          departments={departments}
          selectedDept={selectedDept}
          onSelectDept={(id) => {
            setSelectedDept(id);
            setFormData((prev) => ({ ...prev, department: id }));
          }}
        />

        {/* Section 1: Contact & Project Info */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Project Name *
            </label>
            <input 
              type="text" 
              className="glass-input" 
              placeholder="e.g. Intelligent Onboarding Assistant"
              value={formData.project_name}
              onChange={(e) => handleInputChange('project_name', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Contact Person Name *
            </label>
            <input 
              type="text" 
              className="glass-input" 
              placeholder="e.g. Jean Dupont"
              value={formData.team_contact_name}
              onChange={(e) => handleInputChange('team_contact_name', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Contact Email *
            </label>
            <input 
              type="email" 
              className="glass-input" 
              placeholder="e.g. jean.dupont@segula.fr"
              value={formData.team_contact_email}
              onChange={(e) => handleInputChange('team_contact_email', e.target.value)}
              required
            />
          </div>
        </div>

        {/* Section 2: Requirement Core Fields */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
            Problem Description (What pain point should AI solve?) *
          </label>
          <textarea 
            className="glass-input" 
            rows={3}
            placeholder="Describe the operational challenge in detail (e.g. New employees waste 2 weeks searching HR policy PDFs across shared folders)..."
            value={formData.problem_description}
            onChange={(e) => handleInputChange('problem_description', e.target.value)}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Current Manual Process *
            </label>
            <textarea 
              className="glass-input" 
              rows={2}
              placeholder="How is this handled today? (e.g. Manual SharePoint search and email inquiries)"
              value={formData.current_process}
              onChange={(e) => handleInputChange('current_process', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Expected Outcome / Target Benefit *
            </label>
            <textarea 
              className="glass-input" 
              rows={2}
              placeholder="What is the desired result? (e.g. Instant conversational HR bot answering in under 10 sec)"
              value={formData.expected_outcome}
              onChange={(e) => handleInputChange('expected_outcome', e.target.value)}
              required
            />
          </div>
        </div>

        {/* Section 3: Data & Urgency */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Available Data Description *
            </label>
            <input 
              type="text" 
              className="glass-input" 
              placeholder="e.g. 500 PDF policy documents and FAQ tables"
              value={formData.data_description}
              onChange={(e) => handleInputChange('data_description', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
              Project Urgency / Deadline *
            </label>
            <select 
              className="glass-input"
              value={formData.deadline_urgency}
              onChange={(e) => handleInputChange('deadline_urgency', e.target.value)}
              required
            >
              <option value="low" style={{ background: '#0F172A' }}>Low (Planning phase)</option>
              <option value="medium" style={{ background: '#0F172A' }}>Medium (Targeted this quarter)</option>
              <option value="high" style={{ background: '#0F172A' }}>High (Urgent business need)</option>
            </select>
          </div>
        </div>

        {/* Section 4: Dynamic Department Fields */}
        {dynamicFields && dynamicFields.length > 0 && (
          <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '14px', border: '1px solid var(--border-glass)', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#60A5FA', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Briefcase size={16} /> Department-Specific Context (Corporate & Support)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              {dynamicFields.map((field) => {
                const val = formData.department_specific?.[field.name] ?? '';

                if (field.type === 'select') {
                  let optionsToRender = field.options || [];

                  // Apply dynamic filtering for target_users based on service_area
                  if (field.name === 'target_users') {
                    const currentServiceArea = formData.department_specific?.service_area || 'hr';
                    optionsToRender = SERVICE_AREA_TARGET_USERS[currentServiceArea] || SERVICE_AREA_TARGET_USERS.other;
                  }

                  return (
                    <div key={field.name}>
                      <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', marginBottom: '4px' }}>
                        {field.label} {field.required && '*'}
                      </label>
                      <select 
                        className="glass-input"
                        value={val}
                        onChange={(e) => handleDeptSpecificChange(field.name, e.target.value)}
                      >
                        {optionsToRender.map((opt) => (
                          <option key={opt} value={opt} style={{ background: '#0F172A' }}>
                            {opt.replace(/_/g, ' ').toUpperCase()}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                } else if (field.type === 'boolean') {
                  return (
                    <div key={field.name} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '24px' }}>
                      <input 
                        type="checkbox"
                        id={field.name}
                        checked={Boolean(val)}
                        onChange={(e) => handleDeptSpecificChange(field.name, e.target.checked)}
                        style={{ width: '18px', height: '18px', accentColor: '#3B82F6', cursor: 'pointer' }}
                      />
                      <label htmlFor={field.name} style={{ fontSize: '0.85rem', color: '#E2E8F0', cursor: 'pointer' }}>
                        {field.label}
                      </label>
                    </div>
                  );
                } else if (field.type === 'text' || field.type === 'string') {
                  return (
                    <div key={field.name}>
                      <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', marginBottom: '4px' }}>
                        {field.label} {field.required && '*'}
                      </label>
                      <input
                        type="text"
                        className="glass-input"
                        value={val}
                        onChange={(e) => handleDeptSpecificChange(field.name, e.target.value)}
                        required={field.required}
                      />
                    </div>
                  );
                } else if (field.type === 'number') {
                  return (
                    <div key={field.name}>
                      <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#94A3B8', marginBottom: '4px' }}>
                        {field.label} {field.required && '*'}
                      </label>
                      <input
                        type="number"
                        className="glass-input"
                        value={val}
                        onChange={(e) => handleDeptSpecificChange(field.name, e.target.value)}
                        required={field.required}
                      />
                    </div>
                  );
                }
                return null;
              })}
            </div>
          </div>
        )}

        {/* Section 5: PDF Upload Dropzone */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '8px' }}>
            Attach Requirement PDF Specification (Optional)
          </label>

          {!attachedFile ? (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              style={{
                border: dragActive ? '2px dashed #3B82F6' : '2px dashed rgba(255, 255, 255, 0.15)',
                borderRadius: '14px',
                padding: '24px',
                textAlign: 'center',
                background: dragActive ? 'rgba(59, 130, 246, 0.1)' : 'rgba(15, 23, 42, 0.3)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <UploadCloud size={32} color="#60A5FA" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#E2E8F0' }}>
                Drag and drop your PDF specification document here
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '4px' }}>
                or click to browse files (PDF up to 25MB)
              </div>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                id="pdf-upload-input"
              />
              <label 
                htmlFor="pdf-upload-input" 
                className="btn-secondary" 
                style={{ marginTop: '12px', fontSize: '0.8rem', padding: '6px 14px', display: 'inline-flex' }}
              >
                Browse PDF File
              </label>
            </div>
          ) : (
            <div style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '14px 18px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <FileText size={24} color="#60A5FA" />
                <div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#F8FAFC' }}>
                    {attachedFile.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#93C5FD' }}>
                    {(attachedFile.size / 1024).toFixed(1)} KB • PDF Document attached for automated graph parsing
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                style={{ background: 'transparent', border: 'none', color: '#F87171', cursor: 'pointer', padding: '6px' }}
                title="Remove attachment"
              >
                <Trash2 size={18} />
              </button>
            </div>
          )}
        </div>

        {/* Real-Time Streaming Mode Switch */}
        <div style={{ marginBottom: '20px', padding: '12px 18px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-glass)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Zap size={18} color={streamMode ? '#00F5D4' : '#94A3B8'} />
            <div>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#F8FAFC' }}>
                Real-Time Streaming Mode (SSE)
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
                Live token-by-token generation with interactive AI thought process
              </div>
            </div>
          </div>
          <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={streamMode}
              onChange={(e) => setStreamMode(e.target.checked)}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: streamMode ? '#3B82F6' : '#334155',
                borderRadius: '24px',
                transition: '0.3s',
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  content: '""',
                  height: '18px',
                  width: '18px',
                  left: streamMode ? '22px' : '3px',
                  bottom: '3px',
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  transition: '0.3s',
                }}
              />
            </span>
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="btn-primary"
          disabled={submitting || !isFormValid}
          style={{ 
            width: '100%', 
            justifyContent: 'center', 
            padding: '14px', 
            fontSize: '1rem',
            opacity: (!isFormValid || submitting) ? 0.6 : 1,
            cursor: (!isFormValid || submitting) ? 'not-allowed' : 'pointer'
          }}
          title={!isFormValid ? 'Please fill in all required fields to submit' : 'Submit Requirement'}
        >
          {submitting ? (
            <>
              <Loader2 size={20} className="animate-spin" /> Evaluating Feasibility & Executing Graph...
            </>
          ) : (
            <>
              <Send size={18} /> Submit Requirement & Generate Feasibility Assessment
            </>
          )}
        </button>
      </form>
    </div>
  );
}
