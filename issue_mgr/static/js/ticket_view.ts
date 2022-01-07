// If I were to do this again today I would use fetch() instead
function makeRequest<T>(method: string, url: string, params?: any): Promise<T> {
    return new Promise<T>(((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.onload = function() {
            if (this.status >= 200 && this.status < 300) {
                let res: T = JSON.parse(this.response);
                resolve(res);
            }
            else {
                reject({
                    status: this.status,
                    statusText: this.statusText
                });
            }
        };

        xhr.onerror = function() {
            reject({
                status: this.status,
                statusText: this.statusText
            });
        };

        xhr.send(params);
    }));
}

function joinURL(base: string, segment: string): string {
    if (base.endsWith('/')) {
        return base + segment;
    }
    return base + '/' + segment;
}

interface ServerCategory {
    category_id: number;
    category_name: string;
}

interface ServerUser {
    username: string;
}

function editCategory() {
    let req = makeRequest<ServerCategory[]>("GET", "/api/categories.json", null).then<CategoryOption[]>((res) => {
        console.log(res);
        return res.map(x => {
            return {
                value: x.category_id,
                displayValue: x.category_name
            } as CategoryOption;
        });
    });

    function getInitialCategorySelection(loadedCategories: CategoryOption[]): number | null {
        let currentId = document.getElementById("category").getAttribute("data-categoryId");
        if (currentId == "") {
            return null;
        }

        let id = parseInt(currentId);
        let index = loadedCategories.findIndex((value, index, obj) => value.value == id);
        return (index == -1) ? null : index;
    }

    displayPopup("Update Category", req, getInitialCategorySelection).then(newCat => {
        let req = makeRequest<ServerCategory>("PUT", joinURL(window.location.toString(), "category"), (newCat == null) ? "null" : newCat.value).then((res) => {
            //alert("Successfully updated category!");
            document.getElementById("category").setAttribute("data-categoryId", (res.category_id == null) ? "" : res.category_id.toString());
            document.getElementById("categoryName").innerText = (res.category_name == null) ? "None" : res.category_name;
        }, (err: RequestError) => {
            alert("Failed to update category. Please try again later...\n\nError: " + err.statusText);
        });
    }).catch(reason => {
        console.log("Rejected");
        console.log(reason);
    })

}

function editAssignee() {
    let req = makeRequest<ServerUser[]>("GET", "/api/admins.json", null).then<AssigneeOption[]>( (res) => {
        console.log(res);
        return res.map(x => {
            return {
                value: x.username,
                displayValue: x.username
            } as AssigneeOption;
        });
    });

    function getInitialAssigneeSelection(loadedAssignees: AssigneeOption[]): number | null {
        let currentId = document.getElementById("assignee").getAttribute("data-assignee");
        if (currentId == "") {
            return null
        }

        let index = loadedAssignees.findIndex((value => value.value == currentId));
        return (index == -1) ? null : index;
    }

    displayPopup("Update Assignee", req, getInitialAssigneeSelection).then (newAssignee => {
        let req = makeRequest<ServerUser>("PUT", joinURL(window.location.toString(), "assignee"), (newAssignee == null) ? "" : newAssignee.value).then((res) => {
            // saved new assignee
            document.getElementById("assignee").setAttribute("data-assignee", (res.username == null) ? "" : res.username);
            document.getElementById("assigneeName").innerText = (res.username == null) ? "None" : res.username;
        }, (err: RequestError) => {
            // error saving assignee
            alert("Failed to update assignee. Please try again later...\n\nError: " + err.statusText);
        });

    }, reason => {
        console.log("Rejected");
        console.log(reason);
    });
}

function displayPopup<T extends Option>(title: string, optionsPromise: Promise<T[]>, currentlySelectedOption: (items: T[]) => number | null): Promise<T | null> {
    return new Promise<T>(((resolve, reject) => {
        let selectedIndex: number | null = null;
        let loadedOptions: T[] | null = null;

        let popupContainer = document.createElement("div");
        popupContainer.id = "popupContainer";


        let popup = document.createElement("div");
        popup.id = "popup";
        popup.innerHTML = `<h1>${title}</h1>`;
        popup.addEventListener("click", evt => evt.stopPropagation());

        let optionContainer = document.createElement("ul");
        optionContainer.innerHTML = `
<li>
<p><i class="fas fa-spinner"></i></p>
<p>Loading...</p>
</li>`;

        optionsPromise.then(options => {
            // remove the loading spinner
            optionContainer.innerHTML = "";
            loadedOptions = options;

            selectedIndex = currentlySelectedOption(options);

            for (let i=0; i < options.length; i++) {
                let el = document.createElement("li");
                el.innerHTML = `
                <i class="fas fa-check"></i>
                <span>${options[i].displayValue}</span>
                `;
                el.style.cursor = "pointer";
                if (i == selectedIndex) {
                    el.classList.add("selected");
                }

                el.addEventListener("click", evt => {
                    const parent = optionContainer.getElementsByClassName("selected");
                    Array.prototype.forEach.call(parent, (node: Element) => node.classList.remove("selected"));

                    if (selectedIndex == i) {
                        // deselect that
                        selectedIndex = null;
                    }
                    else {
                        selectedIndex = i;
                        el.classList.add("selected");
                    }
                    evt.stopPropagation();
                });
                optionContainer.appendChild(el);
            }
        })
            .catch(reason => {
                    optionContainer.innerHTML = `
<li>
    <p><i class="fas fa-exclamation-triangle"></i></p>
    <p>${(reason.statusText) ? `${reason.statusText}` : "An unknown error has occurred."}</p>
</li>`;
            });

        popup.appendChild(optionContainer);

        let submitBtn = document.createElement("button");
        submitBtn.innerText = "Save";
        submitBtn.addEventListener("click", evt => {
            closePopup();
            evt.stopPropagation();
            if (loadedOptions == null) {
                return;
            }
            resolve((selectedIndex == null) ? null :  loadedOptions[selectedIndex]);
        });
        popup.appendChild(submitBtn);

        popupContainer.appendChild(popup);
        popupContainer.addEventListener("click", evt => {
            closePopup();
            evt.stopPropagation();
            reject(null);
        });

        document.body.appendChild(popupContainer);
    }));
}

function closePopup() {
    let node = document.getElementById("popupContainer");
    if (node != null) {
        node.parentNode.removeChild(node);
    }
}


function closeTicket() {
    if (confirm("Once closed, this ticket will be unrecoverable. Are you sure you want to continue?")) {
        makeRequest("POST", joinURL(window.location.toString(), "close"), null).then((res) => {
            alert("Ticket Closed");
            window.location.href = "/";
        }, (err: RequestError) => {
            // error closing ticket
            alert("Failed to close ticket. Please try again later...\n\nError: " + err.statusText);
        })
    }
}


interface Option {
    displayValue: string;
    value: string | number;
}

interface CategoryOption extends Option {
    value: number;
}

interface AssigneeOption extends Option {
    value: string;
}

interface RequestError {
    status: number,
    statusText: string
}