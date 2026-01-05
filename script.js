function calculateAge() {
    const dob = new Date(document.getElementById("dob").value);
    const age = new Date(Date.now() - dob.getTime()).getUTCFullYear() - 1970;
    document.getElementById("age").value = age;
}

function book() {
    fetch("http://127.0.0.1:5000/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: document.getElementById("name").value,
            dob: document.getElementById("dob").value,
            age: document.getElementById("age").value,
            gender: document.getElementById("gender").value,
            place: document.getElementById("place").value,
            appointment_date: document.getElementById("appointment_date").value,
            timing: document.getElementById("timing").value
        })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("msg").innerText =
            data.success ? "Appointment booked successfully!" : "Booking failed";
    });
}
