import React, { useState } from "react";
import { addTest } from "../services/testService";

function AddUpdateTest() {

  const [formData, setFormData] = useState({
    testName: "",
    description: "",
    duration: "",
    threshold: ""
  });

  const handleChange = (e) => {

    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });

  };

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      const response = await addTest(formData);

      console.log(response.data);

      alert("Test Added Successfully");

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

          <label htmlFor="testName">
            Test Name
          </label>

          <br />

          <input
            id="testName"
            type="text"
            name="testName"
            value={formData.testName}
            onChange={handleChange}
          />

        </div>

        <br />

        <div>

          <label htmlFor="description">
            Description
          </label>

          <br />

          <input
            id="description"
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
          />

        </div>

        <br />

        <div>

          <label htmlFor="duration">
            Duration
          </label>

          <br />

          <input
            id="duration"
            type="number"
            name="duration"
            value={formData.duration}
            onChange={handleChange}
          />

        </div>

        <br />

        <div>

          <label htmlFor="threshold">
            Threshold
          </label>

          <br />

          <input
            id="threshold"
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