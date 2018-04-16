# time-log-reporter

## Configuration

### Environment variables
The following environment variables must be set in order to work:
| Name                  |Comment                                     |
| ----------------------|--------------------------------------------|
| MAIN_COLOR            | Color of the brand                         |
| HARVEST_ACCOUNT_ID    | For reading logs                           |
| HARVEST_ACCOUNT_TOKEN | For reading logs                           |
| POSTMARK_SERVER_KEY   | For email sending                          |
| FROM_EMAIL            | Email address of origin                    |
| DESTINATION_EMAILS    | Comma separated, recepients of the reports |

## Installation
npm install

## Running
node crons\sendReports.js
node crons\sendAlerts.js
