import React, { useState } from "react";
import { addTest } from "../services/testService";

function AddUpdateTest() {

  const [formData, setFormData] = useState({
    testName: "",
    description: "",
    duration: "",
    threshold: ""
  });

  // handle input changes
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // submit form
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {

      const response = await addTest(formData);

      console.log(response.data);

      alert("Test Added Successfully");

      // clear form
      setFormData({
        testName: "",
        description: "",
        duration: "",
        threshold: ""
      });

    } catch (error) {

      console.error(error);

      alert("Failed to add test");
    }
  };

  return (
    <div style={{ padding: "20px" }}>

      <h2>Add Test</h2>

      <form onSubmit={handleSubmit}>

        <div>
          <label>Test Name</label>
          <br />

          <input
            type="text"
            name="testName"
            value={formData.testName}
            onChange={handleChange}
          />
        </div>

        <br />

        <div>
          <label>Description</label>
          <br />

          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
          />
        </div>

        <br />

        <div>
          <label>Duration</label>
          <br />

          <input
            type="number"
            name="duration"
            value={formData.duration}
            onChange={handleChange}
          />
        </div>

        <br />

        <div>
          <label>Threshold</label>
          <br />

          <input
            type="number"
            name="threshold"
            value={formData.threshold}
            onChange={handleChange}
          />
        </div>

        <br />

        <button type="submit">
          Save Test
        </button>

      </form>
    </div>
  );
}

export default AddUpdateTest;