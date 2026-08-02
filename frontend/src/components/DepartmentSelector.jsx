import React, { useState } from 'react';
import { Building2, Wrench, Car, Rocket, Zap, Lock } from 'lucide-react';

const DEPT_ICONS = {
  corporate_support: Building2,
  manufacturing_engineering: Wrench,
  automotive_software: Car,
  aerospace_defence: Rocket,
  energy_industry: Zap,
};

export default function DepartmentSelector({ departments, selectedDept, onSelectDept }) {
  const [hoveredDisabled, setHoveredDisabled] = useState(null);

  // Fallback defaults if departments API is loading
  const allDepts = departments && departments.length > 0 ? departments : [
    { id: 'corporate_support', name: 'Corporate & Support Services', description: 'HR, IT, Legal, Finance, Knowledge Management', enabled: true },
    { id: 'manufacturing_engineering', name: 'Manufacturing Engineering', description: 'Plant Automation, Robotics, Quality Control', enabled: false },
    { id: 'automotive_software', name: 'Automotive Software', description: 'AUTOSAR, ECU, ADAS Validation', enabled: false },
    { id: 'aerospace_defence', name: 'Aerospace & Defence', description: 'DO-178C, Avionics, Thermal Simulation', enabled: false },
    { id: 'energy_industry', name: 'Energy & Industry', description: 'Grid Optimization, Asset Management', enabled: false },
  ];

  return (
    <div style={{ marginBottom: '28px' }}>
      <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: '#E2E8F0', marginBottom: '12px' }}>
        Select Your Department / Business Unit
      </label>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
        {allDepts.map((dept) => {
          const Icon = DEPT_ICONS[dept.id] || Building2;
          const isEnabled = dept.id === 'corporate_support' || dept.enabled === true;
          const isSelected = selectedDept === dept.id;

          return (
            <div
              key={dept.id}
              onClick={() => {
                if (isEnabled) onSelectDept(dept.id);
              }}
              onMouseEnter={() => !isEnabled && setHoveredDisabled(dept.id)}
              onMouseLeave={() => setHoveredDisabled(null)}
              style={{
                position: 'relative',
                padding: '16px',
                borderRadius: '14px',
                background: isSelected 
                  ? 'rgba(37, 99, 235, 0.25)' 
                  : isEnabled 
                  ? 'rgba(15, 23, 42, 0.6)' 
                  : 'rgba(15, 23, 42, 0.3)',
                border: isSelected 
                  ? '1px solid #3B82F6' 
                  : isEnabled 
                  ? '1px solid rgba(255, 255, 255, 0.08)' 
                  : '1px dashed rgba(255, 255, 255, 0.1)',
                cursor: isEnabled ? 'pointer' : 'not-allowed',
                opacity: isEnabled ? 1 : 0.5,
                transition: 'all 0.2s ease',
                boxShadow: isSelected ? '0 0 20px rgba(59, 130, 246, 0.25)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: isSelected ? '#3B82F6' : 'rgba(30, 41, 59, 0.8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Icon size={18} color={isSelected ? '#FFFFFF' : isEnabled ? '#94A3B8' : '#64748B'} />
                </div>
                {!isEnabled && (
                  <span style={{ fontSize: '0.7rem', color: '#FBBF24', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600, background: 'rgba(245, 158, 11, 0.15)', padding: '2px 8px', borderRadius: '999px' }}>
                    <Lock size={10} /> MVP Lock
                  </span>
                )}
              </div>

              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: isSelected ? '#FFFFFF' : isEnabled ? '#F1F5F9' : '#94A3B8' }}>
                {dept.name || dept.display_name}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '4px', lineHeight: 1.3 }}>
                {dept.description}
              </div>

              {/* Hover Tooltip for disabled departments */}
              {!isEnabled && hoveredDisabled === dept.id && (
                <div style={{
                  position: 'absolute',
                  top: '-36px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: '#1E293B',
                  color: '#FBBF24',
                  border: '1px solid #334155',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  boxShadow: '0 8px 16px rgba(0,0,0,0.4)',
                  zIndex: 20,
                  pointerEvents: 'none',
                }}>
                  🛠️ Still in Development (MVP Phase)
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
