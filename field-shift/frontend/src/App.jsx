import { useEffect, useState } from 'react'
import { ArrowRight, Check, ChevronDown, CircleHelp, Menu, Radio, RotateCcw, Satellite, SlidersHorizontal, X } from 'lucide-react'
import LocationMap from './components/LocationMap'
import MockBadge from './components/MockBadge'
import Results from './components/Results'
import { analyzeFarm, checkHealth } from './services/api'

const apiBase = (import.meta.env.VITE_API_URL?.trim() || 'http://localhost:8000/api').replace(/\/$/, '')
const docsUrl = `${apiBase.replace(/\/api$/, '')}/docs`

const initialFarm = {
  latitude: 32.22,
  longitude: 35.26,
  area_dunams: 10,
  available_water_m3: 500,
  previous_crop: 'wheat',
  priority: 'soil_health',
  mock_temperature_c: 20.8,
  mock_rainfall_mm: 420,
  mock_soil_ph: 7.1,
  mock_organic_matter_percent: 2.7,
}

function Field({ label, name, value, onChange, suffix, step = 'any' }) {
  return (
    <label className="field">
      <span>{label}</span>
      <div className="input-wrap">
        <input name={name} type="number" step={step} value={value} onChange={onChange} required />
        {suffix && <em>{suffix}</em>}
      </div>
    </label>
  )
}

function RangeField({ label, name, value, onChange, min, max, step, suffix }) {
  return (
    <label className="range-field">
      <span><b>{label}</b><output>{value}{suffix}</output></span>
      <input
        type="range"
        name={name}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={onChange}
      />
      <small><span>{min}{suffix}</span><span>{max}{suffix}</span></small>
    </label>
  )
}

export default function App() {
  const [farm, setFarm] = useState(initialFarm)
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('checking')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    checkHealth().then(() => setStatus('online')).catch(() => setStatus('offline'))
  }, [])

  function update(event) {
    const { name, value } = event.target
    const textFields = new Set(['previous_crop', 'priority'])
    setFarm((current) => ({ ...current, [name]: textFields.has(name) ? value : Number(value) }))
  }

  function updateLocation(location) {
    setFarm((current) => ({ ...current, ...location }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await analyzeFarm(farm)
      setResult(data)
      requestAnimationFrame(() => document.querySelector('.results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    } catch (requestError) {
      setError(`${requestError.message}. Make sure FastAPI is running on port 8000.`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <nav className="topbar">
        <a className="brand" href="#top" aria-label="Field Shift home">
          <span className="brand-mark"><i /><i /><i /></span>
          <span>FIELD <b>SHIFT</b></span>
        </a>
        <div className={`nav-links ${mobileOpen ? 'open' : ''}`}>
          <a className="active" href="#planner">Planner</a>
          <a href="#architecture">Architecture</a>
          <a href={docsUrl} target="_blank" rel="noreferrer">API docs</a>
        </div>
        <div className={`api-status ${status}`} title="FastAPI connection status">
          <Radio size={14} /> API {status}
        </div>
        <button className="menu-button" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu">
          {mobileOpen ? <X /> : <Menu />}
        </button>
      </nav>

      <main id="top">
        <header className="hero">
          <div className="hero-kicker"><Satellite size={15} /> NASA SPACE APPS 2026 · PHASE 1</div>
          <h1>Plan what grows <span>next.</span></h1>
          <p>A lightweight architecture demo that turns basic field inputs into transparent, rule-based crop rotation ideas.</p>
          <div className="flow-line" aria-label="Application data flow">
            <span>Farm inputs</span><ArrowRight size={14} /><span>FastAPI rules</span><ArrowRight size={14} /><span>Rotation plan</span>
          </div>
        </header>

        <div className="workspace" id="planner">
          <aside className="planner-panel">
            <div className="panel-heading">
              <div><p className="eyebrow">01 · Field profile</p><h2>Tell us about the farm.</h2></div>
              <MockBadge compact />
            </div>

            <form onSubmit={submit}>
              <fieldset>
                <legend><span>Location</span><small>Required</small></legend>
                <div className="two-col">
                  <Field label="Latitude" name="latitude" value={farm.latitude} onChange={update} step="0.01" suffix="°N" />
                  <Field label="Longitude" name="longitude" value={farm.longitude} onChange={update} step="0.01" suffix="°E" />
                </div>
                <LocationMap
                  latitude={farm.latitude}
                  longitude={farm.longitude}
                  onLocationChange={updateLocation}
                />
              </fieldset>

              <fieldset className="scenario-controls">
                <legend>
                  <span><SlidersHorizontal size={14} /> Tune mock conditions</span>
                  <small>Changes the decision</small>
                </legend>
                <p className="scenario-help">Adjust these demo values, then click Analyze to recalculate crops, risks, and the rotation.</p>
                <div className="range-grid">
                  <RangeField label="Temperature" name="mock_temperature_c" value={farm.mock_temperature_c} onChange={update} min="5" max="40" step="0.5" suffix="°C" />
                  <RangeField label="Annual rainfall" name="mock_rainfall_mm" value={farm.mock_rainfall_mm} onChange={update} min="50" max="1200" step="10" suffix=" mm" />
                  <RangeField label="Soil pH" name="mock_soil_ph" value={farm.mock_soil_ph} onChange={update} min="4" max="9" step="0.1" suffix="" />
                  <RangeField label="Organic matter" name="mock_organic_matter_percent" value={farm.mock_organic_matter_percent} onChange={update} min="0.5" max="8" step="0.1" suffix="%" />
                </div>
              </fieldset>

              <fieldset>
                <legend><span>Resources & history</span><small>Demo inputs</small></legend>
                <div className="two-col">
                  <Field label="Farm area" name="area_dunams" value={farm.area_dunams} onChange={update} step="0.1" suffix="dunams" />
                  <Field label="Irrigation water" name="available_water_m3" value={farm.available_water_m3} onChange={update} step="1" suffix="m³" />
                </div>
                <label className="field">
                  <span>Previously planted crop</span>
                  <div className="select-wrap">
                    <select name="previous_crop" value={farm.previous_crop} onChange={update}>
                      <option value="wheat">Wheat</option>
                      <option value="barley">Barley</option>
                      <option value="tomato">Tomato</option>
                      <option value="chickpea">Chickpea</option>
                      <option value="sunflower">Sunflower</option>
                    </select>
                    <ChevronDown size={17} />
                  </div>
                </label>
                <label className="field">
                  <span>Farmer priority</span>
                  <div className="select-wrap">
                    <select name="priority" value={farm.priority} onChange={update}>
                      <option value="water_saving">Water Saving</option>
                      <option value="soil_health">Soil Health</option>
                      <option value="high_yield">High Yield</option>
                    </select>
                    <ChevronDown size={17} />
                  </div>
                </label>
              </fieldset>

              {error && <div className="error-message" role="alert"><CircleHelp size={17} />{error}</div>}
              <button className="analyze-button" disabled={loading}>
                {loading ? <><span className="spinner" /> Running demo rules…</> : <>Analyze field <ArrowRight size={18} /></>}
              </button>
              <button type="button" className="reset-button" onClick={() => { setFarm(initialFarm); setResult(null); setError('') }}>
                <RotateCcw size={14} /> Reset example
              </button>
            </form>
          </aside>

          <div className="output-panel"><Results data={result} /></div>
        </div>

        <section className="architecture" id="architecture">
          <div><p className="eyebrow">Under the hood</p><h2>Simple by design. Easy to replace.</h2></div>
          <div className="architecture-flow">
            <article><span>01</span><b>React client</b><p>Collects inputs and renders results.</p></article>
            <ArrowRight />
            <article><span>02</span><b>REST / JSON</b><p>Two POST requests through Fetch.</p></article>
            <ArrowRight />
            <article><span>03</span><b>FastAPI</b><p>Validates and applies clear rules.</p></article>
            <ArrowRight />
            <article><span>04</span><b>Mock data</b><p>Future NASA, soil and FAO adapters.</p></article>
          </div>
          <div className="architecture-note"><Check size={16} /> No database · No authentication · No machine learning</div>
        </section>
      </main>

      <footer><span>Field Shift</span><p>Architecture proof of concept · NASA Space Apps 2026</p><MockBadge compact /></footer>
    </div>
  )
}

