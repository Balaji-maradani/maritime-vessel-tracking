# Maritime Frontend Deployment Guide

## 🚀 Pre-Deployment Checklist

### ✅ Environment Configuration
- [ ] `.env` file configured with production API URL
- [ ] Environment variables documented in `.env.example`
- [ ] API endpoints tested and accessible
- [ ] CORS configured on backend for frontend domain

### ✅ Build Optimization
- [ ] Production build tested locally (`npm run build && npm run serve`)
- [ ] Bundle size analyzed (`npm run build:analyze`)
- [ ] No console errors in production build
- [ ] All assets loading correctly

### ✅ Code Quality
- [ ] All TypeScript/ESLint errors resolved
- [ ] No unused dependencies (`npx depcheck`)
- [ ] Code formatted (`npm run format`)
- [ ] Tests passing (`npm test`)

### ✅ Performance
- [ ] Lighthouse score > 90 for Performance
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Bundle size < 250KB gzipped

### ✅ Security
- [ ] No sensitive data in client-side code
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] XSS protection enabled

## 🌐 Render Deployment

### Automatic Deployment
1. **Connect Repository**: Link GitHub repo to Render
2. **Configure Service**:
   - Type: Static Site
   - Build Command: `npm run build`
   - Publish Directory: `build`
   - Auto-Deploy: Yes

3. **Environment Variables**:
   ```
   REACT_APP_API_BASE=https://maritime-backend-q150.onrender.com
   REACT_APP_ENV=production
   NODE_VERSION=18.17.0
   ```

### Manual Deployment
```bash
# Build for production
npm run build

# Test locally
npm run serve

# Deploy to Render (if using Render CLI)
render deploy
```

## 📊 Performance Monitoring

### Key Metrics to Monitor
- **Load Time**: < 3 seconds on 3G
- **Bundle Size**: < 250KB gzipped
- **Memory Usage**: < 50MB typical
- **API Response Time**: < 500ms average

### Monitoring Tools
- Google Lighthouse
- Web Vitals
- Render Analytics
- Browser DevTools

## 🔧 Build Optimization

### Bundle Analysis
```bash
# Analyze bundle size
npm run build:analyze

# Check for unused code
npx webpack-bundle-analyzer build/static/js/*.js
```

### Performance Optimizations Applied
- **Code Splitting**: Automatic with React.lazy()
- **Tree Shaking**: Unused code eliminated
- **Asset Optimization**: Images and CSS minified
- **Caching**: Static assets cached with hash names
- **Compression**: Gzip compression enabled

## 🐛 Troubleshooting

### Common Deployment Issues

**Build Fails on Render**
```bash
# Check Node version compatibility
"engines": {
  "node": ">=16.0.0",
  "npm": ">=8.0.0"
}
```

**Environment Variables Not Working**
- Ensure variables start with `REACT_APP_`
- Check Render dashboard environment settings
- Verify variables are set before build

**API Connection Issues**
- Verify `REACT_APP_API_BASE` is correct
- Check backend CORS settings
- Test API endpoints manually

**Static Assets Not Loading**
- Check `homepage` field in package.json
- Verify build output in `build/` directory
- Check Render publish directory setting

### Debug Commands
```bash
# Check environment variables
echo $REACT_APP_API_BASE

# Test production build locally
npm run build
npm run serve

# Check for build errors
npm run build 2>&1 | tee build.log

# Verify API connectivity
curl -I $REACT_APP_API_BASE/api/vessels/
```

## 📋 Post-Deployment Verification

### Functional Testing
- [ ] Login/logout works
- [ ] All pages load correctly
- [ ] Maps display with vessel data
- [ ] Charts render properly
- [ ] Real-time updates working
- [ ] Role-based access control

### Performance Testing
- [ ] Page load times acceptable
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility
- [ ] API response times

### Security Testing
- [ ] HTTPS enforced
- [ ] No sensitive data exposed
- [ ] Authentication working
- [ ] CORS properly configured

## 🔄 Rollback Plan

### If Deployment Fails
1. **Immediate**: Revert to previous Render deployment
2. **Fix Issues**: Address problems in development
3. **Re-test**: Verify fixes locally
4. **Re-deploy**: Push corrected version

### Rollback Commands
```bash
# Render CLI rollback (if available)
render rollback --service maritime-frontend

# Manual: Revert git commit and push
git revert HEAD
git push origin main
```

## 📈 Monitoring & Maintenance

### Regular Checks
- **Weekly**: Performance metrics review
- **Monthly**: Security updates
- **Quarterly**: Dependency updates

### Update Process
```bash
# Update dependencies
npm update
npm audit fix

# Test updates
npm test
npm run build

# Deploy updates
git commit -am "Update dependencies"
git push origin main
```

## 🎯 Success Criteria

### Deployment Success Indicators
- ✅ Build completes without errors
- ✅ All pages accessible via HTTPS
- ✅ API integration working
- ✅ Real-time features functional
- ✅ Performance metrics within targets
- ✅ No console errors in production

### Performance Targets
- **Lighthouse Performance**: > 90
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: < 250KB gzipped
- **API Response**: < 500ms average

---

**Maritime Frontend Deployment** - Ready for production with optimized performance and monitoring.