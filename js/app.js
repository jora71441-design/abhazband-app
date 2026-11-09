function initApp() {
  try { renderCamps(); } catch (e) { console.error('camps:', e); }
  try { renderRides(); } catch (e) { console.error('rides:', e); }
  try { renderMedia(); } catch (e) { console.error('media:', e); }
  try { calcPressure(); } catch (e) { console.error('pressure:', e); }
  try { initSubscriptionToggle(); } catch (e) { console.error('sub:', e); }
  try { checkAdmin(); } catch (e) { console.error('admin:', e); }
  try { renderVelouyutUI(); } catch (e) { console.error('velouyut:', e); }
  try { checkCampAccessOnLoad(); } catch (e) { console.error('campAccess:', e); }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
