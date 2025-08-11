# 📊 Grafana Dashboard Setup Guide

Since we're running Grafana locally (not in Docker), the dashboard needs to be imported manually.

## 🚀 **Current Status:**

✅ **Grafana is running** at http://localhost:3000  
✅ **Prometheus is running** at http://localhost:9090  
✅ **API metrics are being collected**  
✅ **Dashboard configuration is ready**

## 📋 **Manual Dashboard Setup Steps:**

### **1. Access Grafana**
- Open http://localhost:3000 in your browser
- Login with: **admin** / **admin**

### **2. Add Prometheus Data Source**
1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set **URL** to: `http://localhost:9090`
5. Click **Save & Test**

### **3. Import the Dashboard**
1. Go to **Create** → **Import**
2. Click **Upload JSON file**
3. Select the file: `grafana-dashboard-simple.json`
4. Click **Load**
5. Set **Prometheus** as the data source
6. Click **Import**

## 🎯 **What the Dashboard Shows:**

- **API Request Rate**: Requests per second by endpoint
- **API Response Time**: 95th and 50th percentile response times
- **Total Predictions**: Count of prediction requests
- **Health Check Requests**: Count of health check requests
- **Error Rate**: Error requests per second

## 🔍 **Verify Data is Flowing:**

1. **Check Prometheus Targets**: http://localhost:9090/targets
   - `california-housing-api` should show **UP**
   - `mlflow-ui` should show **UP**

2. **Check API Metrics**: http://localhost:8001/metrics
   - Should show `http_requests_total` counters
   - Should show `http_request_duration_seconds` histograms

3. **Generate Some Traffic**:
   ```bash
   # Make some API calls
   curl http://localhost:8001/health
   curl http://localhost:8001/predict -X POST -H "Content-Type: application/json" -d '{"longitude": -122.23, "latitude": 37.88, "housing_median_age": 41.0, "total_rooms": 880.0, "total_bedrooms": 129.0, "population": 322.0, "households": 126.0, "median_income": 8.3252}'
   ```

## 🎉 **Expected Result:**

After importing the dashboard, you should see:
- **Real-time metrics** from your API
- **Request rate graphs** showing API usage
- **Response time monitoring** for performance tracking
- **Error rate tracking** for reliability monitoring

## 🆘 **Troubleshooting:**

- **No data**: Check if Prometheus is scraping the API
- **Dashboard errors**: Verify Prometheus data source is configured
- **Missing metrics**: Ensure API is generating metrics at `/metrics`

---

**Once the dashboard is imported, you'll have a complete monitoring solution for your MLOps pipeline! 🚀** 