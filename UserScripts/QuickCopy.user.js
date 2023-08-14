// ==UserScript==
// @name         Quick Copy
// @namespace    Torn/Recruitment
// @version      0.4
// @downloadURL  https://raw.githubusercontent.com/NateBream/Cows-Torn-Tools/main/UserScripts/QuickCopy.user.js
// @description  Copy all usernames and links from Advanced Search
// @author       MisterCow
// @match        *://www.torn.com/page.php?sid=UserList*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tampermonkey.net
// @grant        none
// ==/UserScript==

// Variables that will probably change
var buttonName = "COPY PROFILES";
var genericProfileLink = "www.torn.com/profiles.php?XID=";
var hiddenTag = "tt-hidden";


// Add a button
var zNode = document.createElement('div');
zNode.innerHTML = '<button id="myButton" type="button">' + buttonName + '</button>';
zNode.setAttribute('id', 'myContainer');
document.body.appendChild(zNode);

// Activate the newly added button.
document.getElementById("myButton").addEventListener ("click", ButtonClickAction, false);

function ButtonClickAction (zEvent) {
    var x = document.querySelectorAll("a");
    var copyString = "";

    for (var i = 0; i < x.length; i++)
    {
        var cleanText = x[i].textContent.replace(/\s+/g, ' ').trim();
        var cleanLink = x[i].href;

        if(cleanLink.includes(genericProfileLink))
        {
            var parent = x[i].parentElement.parentElement.classList.value;
            if (parent.includes("user") && !parent.includes(hiddenTag))
            {
                // Format for proper pasting into excel/sheets
                copyString += '=HYPERLINK("' + cleanLink + '","' + cleanText + '")\n'
            }
        }
    };

    try
    {
        setTimeout(async()=>console.log(await navigator.clipboard.writeText(copyString)), 250);
    }
    catch (err)
    {
        console.error('Failed to copy: ', err);
    }
}
