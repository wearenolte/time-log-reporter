#!/usr/bin/env node

// Requirements
const requestPromise = require('request-promise'); // https://github.com/request/request-promise
const querystring = require('querystring'); // https://nodejs.org/api/querystring.html
const postmark = require('postmark'); // https://www.npmjs.com/package/postmark

// constants
const MAIN_COLOR = process.env.MAIN_COLOR;

// Internal functions
function getHTMLContent(timePerUser, timePerProjectPerUser) {
    let res = '';
    res += '<div>\n';
    res += '    <h3 style="margin-top:40px;">Hours per user</h3>\n';
    res += '    <table cellspacing="0" style="width: 100%;">\n';
    res += '        <tbody>\n';
    res += '            <tr>\n';
    res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold">User</td>\n`;
    res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold; text-align:right">Hours</td>\n`;
    res += '            </tr>\n';
    Object.keys(timePerUser).forEach((name) => {
        const hours = (timePerUser[name]) ? (Math.round(timePerUser[name] * 10) / 10) : 0;
        res += '<tr>\n';
        res += `    <td style="padding:5px 10px 5px 20px; background-color:#F7F7F7; font-weight:bold">${name}</td>\n`;
        res += `    <td style="padding:5px 10px; background-color:#F7F7F7; text-align:right">${hours}</td>\n`;
        res += '</tr>\n';
    });
    res += '        </tbody>\n';
    res += '    </table>\n';
    res += '</div>\n';
    
    res += '<div>\n';
    res += '    <h3 style="margin-top:40px;">Hours per project and user</h3>\n';
    res += '    <table cellspacing="0" style="width: 100%;">\n';
    res += '        <tbody>\n';
    res += '            <tr>\n';
    res += `                <td colspan=2 style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold">Project/user</td>\n`;
    res += `                <td style="padding:5px 10px; color:white; background-color:${MAIN_COLOR}; font-weight:bold; text-align:right">Hours</td>\n`;
    res += '            </tr>\n';
    Object.keys(timePerProjectPerUser).forEach((projectName) => {
        const userElement = timePerProjectPerUser[projectName];
        res += '                <tr>\n';
        res += `                    <td colspan=2 style="padding:5px 10px 5px 20px; background-color:#F7F7F7; font-weight:bold">${projectName}</td>\n`;
        res += '                    <td style="padding:5px 10px; background-color:#F7F7F7; font-weight:bold; text-align:right">\n';
        res += '                    </td>\n';
        res += '                </tr>\n';
        Object.keys(userElement).forEach((userName) => {
            const element = userElement[userName];
            const hours = (element.hours) ? (Math.round(element.hours * 10) / 10) : 0;
            res += '                    <tr>\n';
            res += `                        <td style="padding:5px 10px 5px 30px; font-weight:bold">${userName}</td>\n`;
            res += `                        <td style="padding:5px 10px; white-space:pre">${element.description }</td>\n`;
            res += `                        <td style="padding:5px 10px; text-align:right">${hours}</td>\n`;
            res += '                    </tr>\n';
        });
    });
    res += '        </tbody>\n';
    res += '    </table>\n';
    res += '</div>\n';
    return res;
}

function addToSummary(dictionary, keys, initialValue, addValue) {
    let iteration = dictionary;
    keys.forEach((key, index) => {
        if (!iteration[key]) {
            if (index !== keys.length - 1) {
                iteration[key] = {};
            } else {
                iteration[key] = initialValue;
            }
        }
        if (index === keys.length - 1) {
            iteration[key] += addValue;
        } else {
            iteration = iteration[key];
        }            
    });
}

function getSummary(timeEntries) {
    let timePerUser = {};
    let timePerProjectPerUser = {};
    timeEntries.forEach((e) => {
        const userName = e.user.name;
        const projectName = e.project.name;
        const taskName = e.task.name;
        const hours = e.hours;
        const notes = (e.notes) ? e.notes : '';

        addToSummary(timePerUser, [userName], 0, hours);
        addToSummary(timePerProjectPerUser, [projectName, userName, 'description'], '', `${taskName}: ${notes}\n`);
        addToSummary(timePerProjectPerUser, [projectName, userName, 'hours'], 0, hours);
    });
    return getHTMLContent(timePerUser, timePerProjectPerUser);
}

// Main
async function main() {
    // Variables
    const now = new Date();
    let yesterday = now;
    yesterday.setDate(yesterday.getDate() - 1);
    const fromDate = yesterday.toISOString().slice(0, 10);
    const toDate = fromDate;
    let timeEntries = [];
    let nextPage = 1;
    
    try {
        // Get time logs
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

        // Send the email
        const postmarkClient = new postmark.Client(process.env.POSTMARK_SERVER_KEY);
        const month = yesterday.toLocaleString('en-us', { month: 'long' });
        await postmarkClient.sendEmail({
            From: process.env.FROM_EMAIL,
            To: process.env.DESTINATION_EMAILS, 
            Subject: `Summary: ${month} ${yesterday.getDate()}, ${yesterday.getFullYear()}`,
            HtmlBody: getSummary(timeEntries),
        });
    } catch (err) {
        console.log('error', err.message);
    }
}

main();
