### Cloud Architecture

![Alt Text](https://github.com/mebestaca/Cloud-Powered-Nutritional-Insights/blob/main/docs/p2%20cloud%20architecture.png)

## Architecture Brief
The dashboard is a static Next.js site on Azure Static Web Apps. In the browser, it calls the Python Azure Function over HTTPS; the Static Web App’s address is on the Function App’s CORS allow-list. The Function reads All_Diets.csv from Azure Blob Storage using a connection string stored in its app settings, then cleans and analyses the data. It returns JSON with the execution time, which Chart.js renders as charts.
