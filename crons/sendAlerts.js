#!/usr/bin/env node

// Requirements
const requestPromise = require('request-promise'); // https://github.com/request/request-promise
const querystring = require('querystring'); // https://nodejs.org/api/querystring.html
const postmark = require('postmark'); // https://www.npmjs.com/package/postmark

// constants
const MAIN_COLOR = process.env.MAIN_COLOR;
const MINIMUM_HOURS = 7;

// Internal functions
function orderByLastName(a, b) {
    if (a.user.lastName === b.user.lastName) {
        return 0;
    }
    return (a.user.lastName < b.user.lastName) ? -1 : 1;
}

function getHTMLContent(regularUsersWithLessThanMinimumHours, contractorsWithLessThanMinimumHours) {
    res = '';
    if (regularUsersWithLessThanMinimumHours.length) {
        res += '<div>\n';
        res += `    <h3>Users that registered less than ${MINIMUM_HOURS} hours</h3>\n`;
        res += '    <table cellspacing="0" style="width: 100%;">\n';
        res += '        <tbody>\n';
        res += '            <tr>\n';
        res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold">User</td>\n`;
        res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold; text-align:right">Hours</td>\n`;
        res += '            </tr>\n';
        regularUsersWithLessThanMinimumHours.forEach((e) => {
            res += '                <tr>\n';
            res += '                    <td style="padding:5px 10px 5px 20px; background-color:#F7F7F7; font-weight:bold">\n';
            res += `                        ${e.user.lastName}, ${e.user.firstName}\n`;
            res += '                    </td>\n';
            res += `                    <td style="padding:5px 10px; background-color:#F7F7F7; text-align:right">${e.hours}</td>\n`;
            res += '                </tr>\n';
        });
        res += '        </tbody>\n';
        res += '    </table>\n';
        res += '</div>\n';
    }
    if (contractorsWithLessThanMinimumHours.length) {
        res += '<div>\n';
        res += `    <h3>Contractors that registered less than ${MINIMUM_HOURS} hours</h3>\n`;
        res += '    <table cellspacing="0" style="width: 100%;">\n';
        res += '        <tbody>\n';
        res += '            <tr>\n';
        res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold">Contractor</td>\n`;
        res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold; text-align:right">Hours</td>\n`;
        res += '            </tr>\n';
        contractorsWithLessThanMinimumHours.forEach((e) => {
            res += '                <tr>\n';
            res += '                    <td style="padding:5px 10px 5px 20px; background-color:#F7F7F7; font-weight:bold">\n';
            res += `                        ${e.user.lastName}, ${e.user.firstName}\n`;
            res += '                    </td>\n';
            res += `                    <td style="padding:5px 10px; background-color:#F7F7F7; text-align:right">${e.hours}</td>\n`;
            res += '                </tr>\n';
        });
        res += '        </tbody>\n';
        res += '    </table>\n';
        res += '</div>\n';
    }
    return res;
}

// Main
async function main() {
    // Variables
    const now = new Date();
    
    if (now.getDay() === 0
        || now.getDay() === 6) {
            return;
    }
    
    const users = {};
    let nextPage = 1;
    
    let yesterday = now;
    yesterday.setDate(yesterday.getDate() - 1);
    const fromDate = yesterday.toISOString().slice(0, 10);
    const toDate = fromDate;
    let timeEntries = [];
    const usersWithLessThanMinimumHours = [];
    const hoursPerUser = {}
    
    try {
        // Users
        while (nextPage) {
            const parameters = {
                is_active: true,
                page: nextPage,
            };
            const requestProperties = {
                method: 'GET',
                uri: `https://api.harvestapp.com/api/v2/users?${querystring.stringify(parameters)}`,
                headers: {
                    Accept: 'application/json',
                    'User-Agent': 'NolteTimeLogReporter',
                    'Harvest-Account-ID': process.env.HARVEST_ACCOUNT_ID,
                    'Authorization': `Bearer ${process.env.HARVEST_ACCOUNT_TOKEN}`,
                },
                json: true,
            };
            const response = await requestPromise(requestProperties);
            
            response.users.forEach((user) => {
                users[user.id] = {
                    id: user.id,
                    firstName: user.first_name,
                    lastName: user.last_name,
                    email: user.email,
                    isContractor: user.is_contractor,
                }
            });
            nextPage = response.next_page;
        }

        // Get time logs
        nextPage = 1;
        while (nextPage) {
            const parameters = {
                from: fromDate,
                to: toDate,
                page: nextPage,
            };
            const requestProperties = {
                method: 'GET',
                uri: `https://api.harvestapp.com/api/v2/time_entries?${querystring.stringify(parameters)}`,
                headers: {
                    Accept: 'application/json',
                    'User-Agent': 'NolteTimeLogReporter',
                    'Harvest-Account-ID': process.env.HARVEST_ACCOUNT_ID,
                    'Authorization': `Bearer ${process.env.HARVEST_ACCOUNT_TOKEN}`,
                },
                json: true,
            };
            const response = await requestPromise(requestProperties);
            if (response.time_entries
                && Array.isArray(response.time_entries)) {
                timeEntries = timeEntries.concat(response.time_entries);
            }
            nextPage = response.next_page;
        }
        
        // Prepare the alerts
        timeEntries.forEach((e) => {
            if (!hoursPerUser[e.user.id]) {
                hoursPerUser[e.user.id] = 0;
            }
            hoursPerUser[e.user.id] = (e.hours) ? parseFloat(e.hours) : 0;
        });
        Object.keys(hoursPerUser).forEach((userId) => {
            if (hoursPerUser[userId] < MINIMUM_HOURS) {
                usersWithLessThanMinimumHours.push({
                    user: users[userId],
                    hours: hoursPerUser[userId],
                });
            }
        });
        Object.keys(users).forEach((userId) => {
            if (!hoursPerUser[userId]) {
                usersWithLessThanMinimumHours.push({
                    user: users[userId],
                    hours: 0.0,
                });
            }
        });

        if (!usersWithLessThanMinimumHours.length) {
            return;
        }

        usersWithLessThanMinimumHours.sort(orderByLastName);
        const regularUsersWithLessThanMinimumHours = [];
        const contractorsWithLessThanMinimumHours = [];
        usersWithLessThanMinimumHours.forEach((u) => {
            if (u.user.isContractor) {
                contractorsWithLessThanMinimumHours.push(u);
            } else {
                regularUsersWithLessThanMinimumHours.push(u);
            }
        });

        // Send the email
        const postmarkClient = new postmark.Client(process.env.POSTMARK_SERVER_KEY);
        const month = yesterday.toLocaleString('en-us', { month: 'long' });
        await postmarkClient.sendEmail({
            From: process.env.FROM_EMAIL,
            To: process.env.DESTINATION_EMAILS, 
            Subject: `Time logging exceptions: ${month} ${yesterday.getDate()}, ${yesterday.getFullYear()}`,
            HtmlBody: getHTMLContent(regularUsersWithLessThanMinimumHours, contractorsWithLessThanMinimumHours),
        });
    } catch (err) {
        console.log('error', err.message);
    }
}

main();
